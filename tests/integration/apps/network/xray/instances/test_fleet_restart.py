"""Exercise independent restart admission and tracking for explicit targets."""

from asyncio import Event, create_subprocess_exec, gather, sleep, timeout
from contextlib import AsyncExitStack
from json import loads
from os import environ
from pathlib import Path
from ssl import create_default_context
from sys import executable
from typing import cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import yaml
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.infra.db.uow import PGUnitOfWork
from sqlalchemy import select

from src.apps.network.nodes.registry.infra.pg.readers.endpoints import (
    NodeEndpointReader,
)
from src.apps.network.xray.instances.app.pipelines.control import (
    XrayControlPipeline,
)
from src.apps.network.xray.instances.domain.results.start import (
    XrayStartOutcome,
    XrayStartTarget,
)
from src.apps.network.xray.instances.infra.broker.config import BrokerConfig
from src.bootstrap.events import create_events
from src.bootstrap.outbox import pending
from src.settings.config import CoreSettings, NatsConfig

from ...nodes.auth import admin_headers
from ..conftest import RunningXrayNode

pytestmark = pytest.mark.integration
_PATH = "/admin/nodes/xray/config-revisions/{revision_id}/restart-operations"


async def test_fleet_restart_reserves_and_tracks_targets_independently(
    app: FastAPI,
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    headers = await admin_headers(
        app, client, mobile="09120000653", role_key="fleet-restart"
    )

    async def node(label: str, *, enabled: bool = True) -> int:
        reply = await client.post(
            "/admin/nodes",
            headers=headers,
            json={
                "name": f"Fleet restart {label}",
                "address": f"fleet-restart-{label}.example.invalid",
                "port": 8443,
                "is_enabled": enabled,
            },
        )
        assert reply.status_code == 201, reply.text
        return reply.json()["data"]["id"]

    first = await node("first")
    second = await node("second")
    disabled = await node("disabled", enabled=False)
    revisions = []
    for label in ("primary", "other"):
        reply = await client.post(
            "/admin/xray/revisions",
            headers=headers,
            json={"config_json": f'{{"remarks":"fleet-restart-{label}"}}'},
        )
        assert reply.status_code == 201, reply.text
        revisions.append(reply.json()["data"]["id"])
    revision_id, alternate_id = revisions
    url = _PATH.format(revision_id=revision_id)
    other = _PATH.format(revision_id=alternate_id)
    held = await client.post(
        f"/admin/nodes/{first}/xray/instances/held/start-operations",
        headers={**headers, "Idempotency-Key": str(uuid4())},
    )
    assert held.status_code == 202, held.text
    targets = [
        {"node_id": id, "instance_id": instance, "request_key": str(uuid4())}
        for id, instance in (
            (first, "edge"),
            (first, "held"),
            (disabled, "edge"),
            (second, "edge"),
            (99999999, "edge"),
        )
    ]
    assert (
        await client.post(url, json={"targets": targets})
    ).status_code == 401
    monkeypatch.setattr(
        NodeEndpointReader,
        "select_endpoint",
        AsyncMock(
            side_effect=AssertionError("Fleet restart used a scalar read")
        ),
    )
    response, replay = await gather(
        client.post(url, headers=headers, json={"targets": targets}),
        client.post(url, headers=headers, json={"targets": targets[::-1]}),
    )
    assert response.status_code == replay.status_code == 202, response.text
    rows = response.json()["data"]
    assert rows == replay.json()["data"][::-1]
    assert [row["status"] for row in rows] == [
        "accepted",
        "active_operation",
        "node_disabled",
        "accepted",
        "node_not_found",
    ]
    operations = [rows[index]["operation"] for index in (0, 3)]
    for operation in operations:
        assert operation["revision_id"] == revision_id
        assert operation["state"] == "queued"
        assert operation["stopped_at"] is None

    conflicting = await client.post(
        other, headers=headers, json={"targets": targets[:1]}
    )
    assert conflicting.status_code == 200, conflicting.text
    assert conflicting.json()["data"][0]["status"] == "request_conflict"
    missing = await client.post(
        _PATH.format(revision_id=99999999),
        headers=headers,
        json={"targets": targets[:1]},
    )
    assert missing.status_code == 404, missing.text
    for selection in ([], targets[:1] * 2, targets[:1] * 17):
        invalid = await client.post(
            url, headers=headers, json={"targets": selection}
        )
        assert invalid.status_code == 422, invalid.text

    applied = await client.post(
        f"/admin/nodes/{first}/xray/instances/apply-only/config-revisions/"
        f"{revision_id}/apply-operations",
        headers={**headers, "Idempotency-Key": str(uuid4())},
    )
    assert applied.status_code == 202, applied.text
    tracking = {
        "targets": [
            {
                "node_id": first,
                "instance_id": "edge",
                "operation_id": operations[0]["id"],
            },
            {
                "node_id": first,
                "instance_id": "held",
                "operation_id": held.json()["data"]["id"],
            },
            {
                "node_id": second,
                "instance_id": "edge",
                "operation_id": operations[1]["id"],
            },
            {
                "node_id": first,
                "instance_id": "apply-only",
                "operation_id": applied.json()["data"]["id"],
            },
        ]
    }
    polled = await client.post(f"{url}/status", headers=headers, json=tracking)
    assert polled.status_code == 200, polled.text
    assert [row["status"] for row in polled.json()["data"]] == [
        "accepted",
        "operation_not_found",
        "accepted",
        "operation_not_found",
    ]
    wrong_revision = await client.post(
        f"{other}/status", headers=headers, json=tracking
    )
    assert [row["status"] for row in wrong_revision.json()["data"]] == [
        "operation_not_found",
    ] * 4

    requested_ids = {operation["id"] for operation in operations}
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        unit = await scope.get(PGUnitOfWork)
        stmt = select(pending.c.payload).where(
            pending.c.queue == BrokerConfig.control_requested
        )
        outbox = await unit.execute(stmt)
        published = [loads(payload)["event"] for payload in outbox.scalars()]
    assert sorted(
        item["operation_id"]
        for item in published
        if item["operation_id"] in requested_ids
    ) == sorted(requested_ids)


async def test_fleet_restart_dispatches_to_independent_real_nodes(
    app: FastAPI,
    client: AsyncClient,
    pg: CoreSettings,
    tmp_path: Path,
    node_pair: tuple[RunningXrayNode, RunningXrayNode],
    node_api_key: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    broker = environ.get("PAPILIOVPN_TEST_NATS_URL")
    if not broker:
        pytest.skip("Set PAPILIOVPN_TEST_NATS_URL to isolated JetStream")
    headers = await admin_headers(
        app, client, mobile="09120000654", role_key="native-fleet-restart"
    )
    node_ids = []
    for index, (grpc_port, http_port, ca, _) in enumerate(node_pair):
        tls = create_default_context()
        ca.configure_trust(tls)
        async with AsyncClient(
            verify=tls, headers={"X-API-Key": node_api_key}
        ) as native:
            started = await native.put(
                f"https://127.0.0.1:{http_port}/v1/xray/instances/edge/execution",
                timeout=10,
            )
            assert started.is_success, started.text
        node = await client.post(
            "/admin/nodes",
            headers=headers,
            json={
                "name": f"Native fleet restart {index}",
                "address": "127.0.0.1",
                "port": grpc_port,
                "api_key": node_api_key,
                "ca_pem": ca.cert_pem.bytes().decode(),
            },
        )
        assert node.status_code == 201, node.text
        node_ids.append(node.json()["data"]["id"])
    saved = await client.post(
        "/admin/xray/revisions",
        headers=headers,
        json={
            "config_json": (
                '{"outbounds":[{"protocol":"freedom","tag":"fleet-restart"}]}'
            )
        },
    )
    assert saved.status_code == 201, saved.text
    revision = saved.json()["data"]
    url = _PATH.format(revision_id=revision["id"])
    accepted = await client.post(
        url,
        headers=headers,
        json={
            "targets": [
                {
                    "node_id": id,
                    "instance_id": "edge",
                    "request_key": str(uuid4()),
                }
                for id in node_ids
            ]
        },
    )
    assert accepted.status_code == 202, accepted.text
    tracking = {
        "targets": [
            {
                key: row[key]
                for key in ("node_id", "instance_id", "operation_id")
            }
            for row in accepted.json()["data"]
        ]
    }
    leading, following = [row["operation_id"] for row in tracking["targets"]]
    entered = Event()
    release = Event()
    restart = XrayControlPipeline._restart

    async def hold_first(
        pipeline: XrayControlPipeline, id: int, target: XrayStartTarget
    ) -> XrayStartOutcome:
        if id == leading:
            entered.set()
            await release.wait()
        elif id == following:
            await entered.wait()
        return await restart(pipeline, id, target)

    monkeypatch.setattr(XrayControlPipeline, "_restart", hold_first)
    pg.nats = NatsConfig(servers=[broker], graceful_timeout=1)
    events = create_events(pg)
    relay_config = tmp_path / "relay.yml"
    relay_config.write_text(yaml.safe_dump(pg.model_dump(mode="json")))

    async def wait_for_restart(index: int) -> list[dict]:
        async with timeout(20):
            while True:
                polled = await client.post(
                    f"{url}/status", headers=headers, json=tracking
                )
                assert polled.status_code == 200, polled.text
                rows = polled.json()["data"]
                if rows[index]["operation"]["state"] not in {
                    "queued",
                    "running",
                }:
                    return rows
                await sleep(0.05)

    async with AsyncExitStack() as stack:
        stack.push_async_callback(events.stop)
        await events.start()
        relay = await create_subprocess_exec(
            str(Path(executable).with_name("faststream")),
            "run",
            "src.entrypoints.outbox:app",
            env={**environ, "PAPILIO_CONFIG": str(relay_config)},
        )

        async def stop_relay() -> None:
            if relay.returncode is None:
                relay.terminate()
                try:
                    async with timeout(5):
                        await relay.wait()
                except TimeoutError:
                    relay.kill()
                    await relay.wait()

        stack.push_async_callback(stop_relay)
        try:
            observed = await wait_for_restart(1)
            first, second = [row["operation"] for row in observed]
            assert first["state"] == "running" and first["stopped_at"] is None
            assert second["state"] == "succeeded", second
            assert second["stopped_at"] is not None
        finally:
            release.set()
        completed = await wait_for_restart(0)
        for row in completed:
            operation = row["operation"]
            assert operation["state"] == "succeeded", operation
            assert operation["stopped_at"] is not None
            assert (
                operation["applied_config_sha256"] == revision["config_sha256"]
            )

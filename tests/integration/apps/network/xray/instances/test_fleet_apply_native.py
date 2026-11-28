"""Assign, apply and stop a saved revision on two real Nodes."""

import ssl
from asyncio import create_subprocess_exec, sleep, timeout, wait_for
from contextlib import AsyncExitStack
from hashlib import sha256
from os import environ
from pathlib import Path
from sys import executable
from typing import Any, cast
from uuid import uuid4

import pytest
import yaml
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from pydantic import SecretStr

from src.apps.network.nodes.registry.app.interfaces.services import (
    INodeService,
)
from src.apps.network.nodes.registry.domain.dtos.records import NodeCreate
from src.bootstrap.events import create_events
from src.settings.config import CoreSettings, NatsConfig

from ...nodes.auth import admin_headers
from ..assignments.test_records import ASSIGNMENT_PATH
from ..conftest import RunningXrayNode
from .test_fleet_start import START_PATH
from .test_fleet_stop import STOP_PATH

pytestmark = pytest.mark.integration


async def test_fleet_apply_reaches_two_nodes_and_reports_failed_peer(
    app: FastAPI,
    client: AsyncClient,
    pg: CoreSettings,
    tmp_path: Path,
    node_pair: tuple[RunningXrayNode, RunningXrayNode],
    node_api_key: str,
) -> None:
    broker = environ.get("PAPILIOVPN_TEST_NATS_URL")
    if not broker:
        pytest.skip("Set PAPILIOVPN_TEST_NATS_URL to isolated JetStream")
    headers = await admin_headers(
        app, client, mobile="09120000769", role_key="native-fleet-apply"
    )
    candidate = '{ "outbounds": [{"protocol":"freedom","tag":"fleet"}] }\n'
    revision = await client.post(
        "/admin/xray/revisions",
        headers=headers,
        json={"config_json": candidate},
    )
    assert revision.status_code == 201, revision.text
    metadata = revision.json()["data"]
    revision_id = metadata["id"]
    digest = sha256(candidate.encode()).hexdigest()
    assert metadata["config_sha256"] == digest
    original = [source.read_bytes() for _, _, _, source in node_pair]
    container = cast(AsyncContainer, app.state.dishka_container)
    targets: list[int] = []
    async with container() as scope:
        nodes = await scope.get(INodeService)
        for index, (grpc_port, _, ca, _) in enumerate(node_pair):
            node = await nodes.create(
                NodeCreate(
                    name=f"Fleet Xray {index}",
                    address="127.0.0.1",
                    port=grpc_port,
                    api_key=SecretStr(node_api_key),
                    ca_pem=ca.cert_pem.bytes().decode(),
                )
            )
            targets.append(node.id)
        absent = await nodes.create(
            NodeCreate(
                name="Fleet unconfigured",
                address="fleet.example.invalid",
                port=81,
            )
        )
    pg.nats = NatsConfig(servers=[broker])
    _, first_http_port, first_ca, _ = node_pair[0]
    tls = ssl.create_default_context()
    first_ca.configure_trust(tls)
    async with AsyncClient(
        verify=tls, headers={"X-API-Key": node_api_key}
    ) as native:
        started = await native.put(
            f"https://127.0.0.1:{first_http_port}/v1/xray/instances/edge/execution",
            timeout=10,
        )
        assert started.is_success, started.text

    assignments = {
        id: ASSIGNMENT_PATH.format(node_id=id, instance_id="edge")
        for id in targets
    }
    expected_before = ("different", "stopped")
    for (id, path), expected in zip(
        assignments.items(), expected_before, strict=True
    ):
        desired = await client.put(
            path, headers=headers, json={"revision_id": revision_id}
        )
        assert desired.status_code == 200, desired.text
        comparison = await client.get(f"{path}/comparison", headers=headers)
        assert comparison.status_code == 200, comparison.text
        view = comparison.json()["data"]
        assert view["desired"]["revision_id"] == revision_id
        assert view["state"] == expected, (id, view)
        assert view["observed"]["received_at"] is not None
        if expected == "different":
            assert (
                view["observed"]["instance"]["applied_config_sha256"]
                == sha256(original[0]).hexdigest()
            )

    order = [*targets, absent.id]
    url = f"/admin/nodes/xray/config-revisions/{revision_id}/apply-operations"
    selection = {
        "targets": [
            {"node_id": id, "instance_id": "edge", "request_key": str(uuid4())}
            for id in order
        ]
    }
    accepted = await client.post(url, headers=headers, json=selection)
    assert accepted.status_code == 202, accepted.text
    rows = accepted.json()["data"]
    assert [row["operation"]["state"] for row in rows] == ["queued"] * 3
    assert [row["node_id"] for row in rows] == order
    tracking = {
        "targets": [
            {
                field: row[field]
                for field in ("node_id", "instance_id", "operation_id")
            }
            for row in rows
        ]
    }
    events = create_events(pg)
    relay_config = tmp_path / "fleet-apply-relay.yml"
    relay_config.write_text(yaml.safe_dump(pg.model_dump(mode="json")))
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
                    await wait_for(relay.wait(), timeout=5)
                except TimeoutError:
                    relay.kill()
                    await relay.wait()

        stack.push_async_callback(stop_relay)
        async with timeout(15):
            while True:
                reply = await client.post(
                    f"{url}/status", headers=headers, json=tracking
                )
                assert reply.status_code == 200, reply.text
                final = reply.json()["data"]
                if all(
                    row["operation"]["state"] not in {"queued", "running"}
                    for row in final
                ):
                    break
                await sleep(0.05)
        assert [row["operation"]["state"] for row in final] == [
            "succeeded",
            "succeeded",
            "failed",
        ]
        assert final[2]["operation"]["reason"] == "not_configured"
        for row in final[:2]:
            assert row["operation"]["applied_config_sha256"] == digest
            comparison = await client.get(
                f"{assignments[row['node_id']]}/comparison", headers=headers
            )
            assert comparison.status_code == 200, comparison.text
            view = comparison.json()["data"]
            assert view["state"] == "matched", view
            observed = view["observed"]
            assert observed["status"] == "observed"
            assert observed["instance"]["state"] == "ready"
            assert observed["instance"]["applied_config_sha256"] == digest
        assert [
            source.read_bytes() for _, _, _, source in node_pair
        ] == original
        replay = await client.post(url, headers=headers, json=selection)
        assert replay.status_code == 202, replay.text
        assert replay.json()["data"] == final
        cleared = await client.delete(assignments[order[0]], headers=headers)
        assert cleared.status_code == 204, cleared.text
        instance = f"/admin/nodes/{order[0]}/xray/instances/edge"
        unchanged = await client.get(instance, headers=headers)
        current = unchanged.json()["data"]["instance"]
        assert (
            current["state"] == "ready"
            and current["applied_config_sha256"] == digest
        )
        await _verify_fleet_stop(client, headers, order)
        comparison = await client.get(
            f"{assignments[order[1]]}/comparison", headers=headers
        )
        assert comparison.status_code == 200, comparison.text
        observed = comparison.json()["data"]
        assert observed["desired"]["revision_id"] == revision_id
        assert observed["state"] == "stopped", observed
        assert [
            source.read_bytes() for _, _, _, source in node_pair
        ] == original
        local_sources = [original[0], original[1] + b"\n"]
        node_pair[1][3].write_bytes(local_sources[1])
        started = await _execute_fleet(client, headers, START_PATH, order)
        for row, source in zip(started[:2], local_sources, strict=True):
            assert (
                row["operation"]["applied_config_sha256"]
                == sha256(source).hexdigest()
            )
        comparison = await client.get(
            f"{assignments[order[1]]}/comparison", headers=headers
        )
        assert comparison.status_code == 200, comparison.text
        view = comparison.json()["data"]
        assert view["desired"]["revision_id"] == revision_id
        assert view["state"] == "different"
        assert [
            source.read_bytes() for _, _, _, source in node_pair
        ] == local_sources


async def _verify_fleet_stop(
    client: AsyncClient, headers: dict[str, str], order: list[int]
) -> None:
    await _execute_fleet(client, headers, STOP_PATH, order)
    for id in order[:2]:
        url = f"/admin/nodes/{id}/xray/instances/edge"
        observed = await client.get(url, headers=headers)
        assert observed.status_code == 200, observed.text
        instance = observed.json()["data"]["instance"]
        assert instance["state"] == "stopped"
        assert instance["applied_config_sha256"] is None


async def _execute_fleet(
    client: AsyncClient, headers: dict[str, str], path: str, order: list[int]
) -> list[dict[str, Any]]:
    selection = {
        "targets": [
            {"node_id": id, "instance_id": "edge", "request_key": str(uuid4())}
            for id in order
        ]
    }
    queued = await client.post(path, headers=headers, json=selection)
    assert queued.status_code == 202, queued.text
    rows = queued.json()["data"]
    tracking = {
        "targets": [
            {
                field: row[field]
                for field in ("node_id", "instance_id", "operation_id")
            }
            for row in rows
        ]
    }
    async with timeout(15):
        while True:
            reply = await client.post(
                f"{path}/status", headers=headers, json=tracking
            )
            assert reply.status_code == 200, reply.text
            final = reply.json()["data"]
            states = [row["operation"]["state"] for row in final]
            if all(state not in {"queued", "running"} for state in states):
                break
            await sleep(0.05)
    assert [row["node_id"] for row in final] == order
    assert states == ["succeeded", "succeeded", "failed"], final
    assert final[-1]["operation"]["reason"] == "not_configured"
    replay = await client.post(path, headers=headers, json=selection)
    assert replay.status_code == 202, replay.text
    assert replay.json()["data"] == final
    return final

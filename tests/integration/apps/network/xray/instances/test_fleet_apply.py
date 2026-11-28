"""Check independent fleet admission over the shared Xray execution slots."""

from asyncio import gather
from collections.abc import Sequence
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.errors.exceptions import ConflictException
from papilio_tasks.apps.events.publishers.base import Publication
from papilio_tasks.apps.outbox import OutboxWriter
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import create_async_engine

from src.apps.network.xray.instances.domain.events.apply import (
    XrayApplyRequested,
)
from src.apps.network.xray.instances.infra.broker.config import BrokerConfig
from src.bootstrap.outbox import pending
from src.settings.config import CoreSettings

from ...nodes.auth import admin_headers

pytestmark = pytest.mark.integration
_PATH = "/admin/nodes/xray/config-revisions/{revision_id}/apply-operations"


async def test_fleet_apply_keeps_partial_admission_and_per_target_identity(
    app: FastAPI,
    client: AsyncClient,
) -> None:
    headers = await admin_headers(
        app, client, mobile="09120000770", role_key="fleet-apply"
    )

    async def node(name: str, enabled: bool = True) -> int:
        reply = await client.post(
            "/admin/nodes",
            headers=headers,
            json={
                "name": name,
                "address": f"{name}.example.invalid",
                "port": 81,
                "is_enabled": enabled,
            },
        )
        assert reply.status_code == 201, reply.text
        return reply.json()["data"]["id"]

    free, busy, disabled = (
        await node("apply-free"),
        await node("apply-busy"),
        await node("apply-disabled", False),
    )
    revisions = []
    for value in ('{"remarks":"fleet-apply"}', '{"remarks":"fleet-other"}'):
        reply = await client.post(
            "/admin/xray/revisions",
            headers=headers,
            json={"config_json": value},
        )
        assert reply.status_code == 201, reply.text
        revisions.append(reply.json()["data"]["id"])
    url = _PATH.format(revision_id=revisions[0])
    busy_key = str(uuid4())
    held = await client.post(
        f"/admin/nodes/{busy}/xray/instances/edge/start-operations",
        headers={**headers, "Idempotency-Key": busy_key},
    )
    assert held.status_code == 202, held.text
    target = {
        "node_id": free,
        "instance_id": "edge",
        "request_key": str(uuid4()),
    }
    body = {
        "targets": [
            {**target, "node_id": disabled},
            target,
            {**target, "node_id": busy},
            {**target, "node_id": busy, "instance_id": "other"},
            {**target, "node_id": 99999999},
        ]
    }
    first, replay = await gather(
        client.post(url, headers=headers, json=body),
        client.post(
            url,
            headers=headers,
            json={"targets": list(reversed(body["targets"]))},
        ),
    )
    assert first.status_code == replay.status_code == 202, first.text
    rows = first.json()["data"]
    assert list(reversed(replay.json()["data"])) == rows
    assert [item["status"] for item in rows] == [
        "node_disabled",
        "accepted",
        "active_operation",
        "accepted",
        "node_not_found",
    ]
    operation = rows[1]["operation"]
    assert (
        operation["revision_id"] == revisions[0]
        and operation["state"] == "queued"
    )
    child_url = (
        f"/admin/nodes/{free}/xray/instances/edge/config-revisions/"
        f"{revisions[0]}/apply-operations"
    )
    single = await client.get(
        f"{child_url}/{operation['id']}", headers=headers
    )
    assert single.json()["data"] == operation
    replay_single = await client.post(
        child_url,
        headers={**headers, "Idempotency-Key": target["request_key"]},
    )
    assert replay_single.json()["data"] == operation
    bad = await client.post(
        _PATH.format(revision_id=revisions[1]),
        headers=headers,
        json={"targets": [target]},
    )
    assert bad.status_code == 200, bad.text
    assert bad.json()["data"][0]["status"] == "request_conflict"
    for targets in (
        [target, {**target, "request_key": str(uuid4())}],
        [target] * 17,
        [],
    ):
        bad = await client.post(
            url, headers=headers, json={"targets": targets}
        )
        assert bad.status_code == 422, bad.text
    missing = await client.post(
        _PATH.format(revision_id=99999999),
        headers=headers,
        json={"targets": [target]},
    )
    assert missing.status_code == 404, missing.text

    tracking = {
        "node_id": free,
        "instance_id": "edge",
        "operation_id": operation["id"],
    }
    observed = await client.post(
        f"{url}/status",
        headers=headers,
        json={
            "targets": [
                tracking,
                {**tracking, "node_id": disabled},
                tracking,
            ]
        },
    )
    assert observed.status_code == 200, observed.text
    records = observed.json()["data"]
    assert [item["status"] for item in records] == [
        "accepted",
        "operation_not_found",
        "accepted",
    ]
    assert records[0]["operation"] == records[2]["operation"] == operation
    assert records[1]["operation"] is None


async def test_fleet_apply_rolls_back_the_operations_with_their_outbox(
    app: FastAPI,
    client: AsyncClient,
    pg: CoreSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert pg.db is not None
    headers = await admin_headers(
        app, client, mobile="09120000768", role_key="fleet-atomic"
    )
    created = await client.post(
        "/admin/nodes",
        headers=headers,
        json={
            "name": "Fleet rollback",
            "address": "fleet-rollback.example.invalid",
            "port": 81,
        },
    )
    assert created.status_code == 201, created.text
    id = created.json()["data"]["id"]
    revision = await client.post(
        "/admin/xray/revisions",
        headers=headers,
        json={"config_json": '{"remarks":"fleet-atomic"}'},
    )
    assert revision.status_code == 201, revision.text
    url = _PATH.format(revision_id=revision.json()["data"]["id"])
    targets = [
        {"node_id": id, "instance_id": instance, "request_key": str(uuid4())}
        for instance in ("east", "west")
    ]
    captured: list[int] = []
    append = OutboxWriter.append_batch

    async def fail_after_native_insert[T](
        self: OutboxWriter,
        publisher: Publication[T],
        events: Sequence[T],
        **options: object,
    ) -> None:
        await append(self, publisher, events, **options)
        for event in events:
            assert isinstance(event, XrayApplyRequested)
            captured.append(event.operation_id)
        raise ConflictException(
            message="Isolated rollback check",
            message_code="fleet_test_rollback",
            unique_dict={},
        )

    engine = create_async_engine(pg.db.dsn)

    async def pending_apply_count() -> int:
        async with engine.connect() as connection:
            stmt = (
                select(func.count())
                .select_from(pending)
                .where(pending.c.queue == BrokerConfig.apply_requested)
            )
            return (await connection.execute(stmt)).scalar_one()

    try:
        before = await pending_apply_count()
        with monkeypatch.context() as patch:
            patch.setattr(
                OutboxWriter, "append_batch", fail_after_native_insert
            )
            failure = await client.post(
                url, headers=headers, json={"targets": targets}
            )
        assert failure.status_code == 409, failure.text
        assert failure.json()["error"]["message_code"] == "fleet_test_rollback"
        assert len(captured) == 2
        assert await pending_apply_count() == before

        tracked = await client.post(
            f"{url}/status",
            headers=headers,
            json={
                "targets": [
                    {
                        "node_id": id,
                        "instance_id": item["instance_id"],
                        "operation_id": op,
                    }
                    for item, op in zip(targets, captured, strict=True)
                ]
            },
        )
        assert [row["status"] for row in tracked.json()["data"]] == [
            "operation_not_found"
        ] * 2
        accepted = await client.post(
            url, headers=headers, json={"targets": targets}
        )
        assert accepted.status_code == 202, accepted.text
        assert await pending_apply_count() == before + 2
    finally:
        await engine.dispose()

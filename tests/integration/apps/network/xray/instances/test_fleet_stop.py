"""Verify bounded Stop admission and tracking against PostgreSQL."""

from asyncio import gather
from collections.abc import Sequence
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.errors.exceptions import ConflictException
from papilio_tasks.apps.events.publishers.base import Publication
from papilio_tasks.apps.outbox import OutboxWriter
from sqlalchemy import event, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import create_async_engine

from src.apps.network.xray.instances.domain.events.control import (
    XrayControlRequested,
)
from src.apps.network.xray.instances.infra.broker.config import BrokerConfig
from src.bootstrap.outbox import pending
from src.settings.config import CoreSettings

from ...nodes.auth import admin_headers

pytestmark = pytest.mark.integration
STOP_PATH = "/admin/nodes/xray/instances/stop-operations"


async def test_stop_selection_preserves_conflicts_and_replays(
    app: FastAPI, client: AsyncClient
) -> None:
    headers = await admin_headers(
        app, client, mobile="09120000685", role_key="fleet-stop"
    )

    async def register(name: str, enabled: bool = True) -> int:
        response = await client.post(
            "/admin/nodes",
            headers=headers,
            json={
                "name": name,
                "address": f"{name}.example.invalid",
                "port": 81,
                "is_enabled": enabled,
            },
        )
        assert response.status_code == 201, response.text
        return response.json()["data"]["id"]

    live = await register("stop-live")
    disabled = await register("stop-disabled", False)
    busy_key = str(uuid4())
    start = await client.post(
        f"/admin/nodes/{live}/xray/instances/held/start-operations",
        headers={**headers, "Idempotency-Key": busy_key},
    )
    assert start.status_code == 202, start.text
    target = {
        "node_id": live,
        "instance_id": "east",
        "request_key": str(uuid4()),
    }
    targets = [
        {**target, "node_id": disabled},
        target,
        {**target, "instance_id": "held"},
        {**target, "instance_id": "west"},
        {**target, "node_id": 99999999},
    ]
    first, repeated = await gather(
        client.post(STOP_PATH, headers=headers, json={"targets": targets}),
        client.post(
            STOP_PATH, headers=headers, json={"targets": targets[::-1]}
        ),
    )
    assert first.status_code == repeated.status_code == 202, first.text
    rows = first.json()["data"]
    assert "no-store" in first.headers["Cache-Control"]
    assert repeated.json()["data"] == rows[::-1]
    assert [row["status"] for row in rows] == [
        "node_disabled",
        "accepted",
        "active_operation",
        "accepted",
        "node_not_found",
    ]
    held = {**target, "instance_id": "held", "request_key": busy_key}
    conflict = await client.post(
        STOP_PATH, headers=headers, json={"targets": [held]}
    )
    assert conflict.status_code == 200, conflict.text
    assert conflict.json()["data"][0]["status"] == "request_conflict"
    assert rows[1]["operation"]["state"] == "queued"
    operation = rows[1]["operation"]
    single = await client.post(
        f"/admin/nodes/{live}/xray/instances/east/stop-operations",
        headers={**headers, "Idempotency-Key": str(target["request_key"])},
    )
    assert single.status_code == 202, single.text
    assert single.json()["data"] == operation

    tracking = {
        "node_id": live,
        "instance_id": "east",
        "operation_id": operation["id"],
    }
    result = await client.post(
        f"{STOP_PATH}/status",
        headers=headers,
        json={
            "targets": [
                tracking,
                {
                    **tracking,
                    "instance_id": "held",
                    "operation_id": start.json()["data"]["id"],
                },
                {**tracking, "node_id": disabled},
                tracking,
            ]
        },
    )
    assert result.status_code == 200, result.text
    statuses = result.json()["data"]
    assert [row["status"] for row in statuses] == [
        "accepted",
        "operation_not_found",
        "operation_not_found",
        "accepted",
    ]
    assert statuses[0]["operation"] == statuses[-1]["operation"] == operation
    for invalid in (
        [],
        [target, {**target, "request_key": str(uuid4())}],
        [target] * 17,
    ):
        bad = await client.post(
            STOP_PATH, headers=headers, json={"targets": invalid}
        )
        assert bad.status_code == 422, bad.text


async def test_stop_batch_has_fixed_sql_and_shares_the_outbox_transaction(
    app: FastAPI,
    client: AsyncClient,
    pg: CoreSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    headers = await admin_headers(
        app, client, mobile="09120000686", role_key="fleet-stop-atomic"
    )
    targets = []
    for index in range(8):
        registered = await client.post(
            "/admin/nodes",
            headers=headers,
            json={
                "name": f"Fleet Stop batch {index}",
                "address": f"fleet-stop-batch-{index}.example.invalid",
                "port": 81,
            },
        )
        assert registered.status_code == 201, registered.text
        targets.append(
            {
                "node_id": registered.json()["data"]["id"],
                "instance_id": "edge",
                "request_key": str(uuid4()),
            }
        )
    statements: list[str] = []

    def capture_sql(
        _connection: object,
        _cursor: object,
        statement: str,
        _parameters: object,
        _context: object,
        _executemany: bool,
    ) -> None:
        sql = statement.strip().lower()
        if any(
            table in sql
            for table in ("tbl_nodes", "tbl_xray_start", "event_outbox")
        ):
            statements.append(sql.split(None, 1)[0])

    event.listen(Engine, "before_cursor_execute", capture_sql)
    try:
        for selection in (targets[:1], targets[1:]):
            statements.clear()
            accepted = await client.post(
                STOP_PATH, headers=headers, json={"targets": selection}
            )
            assert accepted.status_code == 202, accepted.text
            assert statements == [
                "select",
                "select",
                "update",
                "insert",
                "insert",
            ]
            keys = [
                {
                    field: row[field]
                    for field in ("node_id", "instance_id", "operation_id")
                }
                for row in accepted.json()["data"]
            ]
            statements.clear()
            tracked = await client.post(
                f"{STOP_PATH}/status", headers=headers, json={"targets": keys}
            )
            assert tracked.status_code == 200, tracked.text
            assert statements == ["select"]
    finally:
        event.remove(Engine, "before_cursor_execute", capture_sql)

    captured: list[int] = []
    append_batch = OutboxWriter.append_batch

    async def fail_after_append[T](
        self: OutboxWriter,
        publisher: Publication[T],
        events: Sequence[T],
        **options: object,
    ) -> None:
        await append_batch(self, publisher, events, **options)
        for item in events:
            assert isinstance(item, XrayControlRequested)
            captured.append(item.operation_id)
        raise ConflictException(
            message="Isolated Stop rollback",
            message_code="fleet_stop_test_rollback",
            unique_dict={},
        )

    assert pg.db is not None
    engine = create_async_engine(pg.db.dsn)

    async def control_count() -> int:
        async with engine.connect() as connection:
            stmt = (
                select(func.count())
                .select_from(pending)
                .where(pending.c.queue == BrokerConfig.control_requested)
            )
            return (await connection.execute(stmt)).scalar_one()

    try:
        before = await control_count()
        replay = await client.post(
            STOP_PATH, headers=headers, json={"targets": targets}
        )
        assert replay.status_code == 202, replay.text
        assert await control_count() == before
        rolled_back = [
            {**row, "instance_id": f"rollback-{index}"}
            for index, row in enumerate(targets[:2])
        ]
        with monkeypatch.context() as patch:
            patch.setattr(OutboxWriter, "append_batch", fail_after_append)
            failed = await client.post(
                STOP_PATH, headers=headers, json={"targets": rolled_back}
            )
        assert failed.status_code == 409, failed.text
        assert (
            failed.json()["error"]["message_code"]
            == "fleet_stop_test_rollback"
        )
        assert len(captured) == 2
        assert await control_count() == before
        tracking = [
            {
                "node_id": target["node_id"],
                "instance_id": target["instance_id"],
                "operation_id": id,
            }
            for target, id in zip(rolled_back, captured, strict=True)
        ]
        observed = await client.post(
            f"{STOP_PATH}/status", headers=headers, json={"targets": tracking}
        )
        assert observed.status_code == 200, observed.text
        assert [row["status"] for row in observed.json()["data"]] == [
            "operation_not_found",
            "operation_not_found",
        ]
    finally:
        await engine.dispose()

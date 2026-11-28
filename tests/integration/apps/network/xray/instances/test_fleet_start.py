"""Verify local-source Start admission and tracking against PostgreSQL."""

from json import loads
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

from src.apps.network.xray.instances.infra.broker.config import BrokerConfig
from src.bootstrap.outbox import pending
from src.settings.config import CoreSettings

from ...nodes.auth import admin_headers

pytestmark = pytest.mark.integration
START_PATH = "/admin/nodes/xray/instances/start-operations"


async def test_fleet_start_tracks_only_local_source_operations(
    app: FastAPI, client: AsyncClient, pg: CoreSettings
) -> None:
    headers = await admin_headers(
        app, client, mobile="09120000687", role_key="fleet-start"
    )
    node = await client.post(
        "/admin/nodes",
        headers=headers,
        json={
            "name": "Fleet Start",
            "address": "fleet-start.example.invalid",
            "port": 81,
        },
    )
    assert node.status_code == 201, node.text
    node_id = node.json()["data"]["id"]
    revision = await client.post(
        "/admin/xray/revisions",
        headers=headers,
        json={"config_json": '{"remarks":"fleet-start-is-local"}'},
    )
    assert revision.status_code == 201, revision.text
    revision_id = revision.json()["data"]["id"]
    apply_key = str(uuid4())
    base = f"/admin/nodes/{node_id}/xray/instances"
    applied = await client.post(
        f"{base}/applied/config-revisions/{revision_id}/apply-operations",
        headers={**headers, "Idempotency-Key": apply_key},
    )
    assert applied.status_code == 202, applied.text
    local = {
        "node_id": node_id,
        "instance_id": "local",
        "request_key": str(uuid4()),
    }
    payload = {
        "targets": [
            {**local, "instance_id": "applied", "request_key": apply_key},
            local,
            {**local, "node_id": 99999999},
        ]
    }
    denied = await client.post(START_PATH, json=payload)
    assert denied.status_code == 401, denied.text
    reply = await client.post(START_PATH, headers=headers, json=payload)
    assert reply.status_code == 202, reply.text
    assert "no-store" in reply.headers["Cache-Control"]
    rows = reply.json()["data"]
    assert [row["status"] for row in rows] == [
        "request_conflict",
        "accepted",
        "node_not_found",
    ]
    operation = rows[1]["operation"]
    assert operation["state"] == "queued"
    scalar = await client.post(
        f"{base}/local/start-operations",
        headers={**headers, "Idempotency-Key": local["request_key"]},
    )
    assert scalar.status_code == 202, scalar.text
    assert scalar.json()["data"] == operation
    repeated = await client.post(START_PATH, headers=headers, json=payload)
    assert repeated.json()["data"] == rows
    busy = await client.post(
        START_PATH,
        headers=headers,
        json={"targets": [{**local, "instance_id": "applied"}]},
    )
    assert busy.status_code == 200, busy.text
    assert busy.json()["data"][0]["status"] == "active_operation"

    tracked = {
        "node_id": node_id,
        "instance_id": "local",
        "operation_id": operation["id"],
    }
    result = await client.post(
        f"{START_PATH}/status",
        headers=headers,
        json={
            "targets": [
                tracked,
                {
                    **tracked,
                    "instance_id": "applied",
                    "operation_id": applied.json()["data"]["id"],
                },
                tracked,
            ]
        },
    )
    assert result.status_code == 200, result.text
    evidence = result.json()["data"]
    assert [row["status"] for row in evidence] == [
        "accepted",
        "operation_not_found",
        "accepted",
    ]
    assert evidence[0]["operation"] == evidence[-1]["operation"] == operation
    assert evidence[1]["operation"] is None

    duplicate = await client.post(
        START_PATH,
        headers=headers,
        json={"targets": [local, {**local, "request_key": str(uuid4())}]},
    )
    assert duplicate.status_code == 422, duplicate.text
    assert pg.db is not None
    engine = create_async_engine(pg.db.dsn)
    try:
        async with engine.connect() as connection:
            stmt = select(pending.c.payload).where(
                pending.c.queue == BrokerConfig.start_requested
            )
            bodies = (await connection.execute(stmt)).scalars()
            events = (loads(body)["event"] for body in bodies)
            assert [
                event
                for event in events
                if event["operation_id"] == operation["id"]
            ] == [{"operation_id": operation["id"]}]
    finally:
        await engine.dispose()

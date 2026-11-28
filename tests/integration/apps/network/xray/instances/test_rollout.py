"""Check durable ordering and idempotency at rollout admission."""

from asyncio import gather
from datetime import timedelta
from typing import cast
from uuid import uuid4

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.utils.dates import utc_now
from sqlalchemy import update
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import col

from src.apps.network.xray.instances.app.pipelines.rollout import (
    RestartRolloutPipeline,
)
from src.apps.network.xray.instances.infra.pg.tables import XrayStartTable
from src.settings.config import CoreSettings

from ...nodes.auth import admin_headers

pytestmark = pytest.mark.integration
ROLLOUT_PATH = (
    "/admin/nodes/xray/config-revisions/{revision_id}/restart-rollouts"
)


async def test_rollout_creates_only_first_operation(
    app: FastAPI,
    client: AsyncClient,
    pg: CoreSettings,
) -> None:
    headers = await admin_headers(
        app, client, mobile="09120000786", role_key="xray-rollout-admission"
    )
    ids = []
    for suffix in ("one", "two"):
        reply = await client.post(
            "/admin/nodes",
            headers=headers,
            json={
                "name": f"rollout-{suffix}",
                "address": f"rollout-{suffix}.example.invalid",
                "port": 81,
            },
        )
        assert reply.status_code == 201, reply.text
        ids.append(reply.json()["data"]["id"])
    revision = await client.post(
        "/admin/xray/revisions",
        headers=headers,
        json={"config_json": '{"remarks":"rollout-admission"}'},
    )
    assert revision.status_code == 201, revision.text
    revision_id = revision.json()["data"]["id"]
    base = ROLLOUT_PATH.format(revision_id=revision_id)
    selected = [{"node_id": id, "instance_id": "edge"} for id in ids]
    write = {**headers, "Idempotency-Key": str(uuid4())}
    first, replay = await gather(
        *(
            client.post(base, headers=write, json={"targets": selected})
            for _ in range(2)
        )
    )
    assert first.status_code == replay.status_code == 202, first.text
    result = first.json()["data"]
    assert replay.json()["data"] == result
    assert result["state"] == "running"
    assert [target["node_id"] for target in result["steps"]] == ids
    assert [target["state"] for target in result["steps"]] == [
        "queued",
        "pending",
    ]
    assert result["steps"][0]["operation"]["revision_id"] == revision_id
    assert result["steps"][1]["operation"] is None
    changed = await client.post(
        base, headers=write, json={"targets": list(reversed(selected))}
    )
    assert changed.status_code == 409, changed.text
    duplicate = await client.post(
        base, headers=write, json={"targets": [selected[0]] * 2}
    )
    assert duplicate.status_code == 422, duplicate.text
    read = await client.get(f"{base}/{result['id']}", headers=headers)
    assert read.json()["data"] == result
    assert (await client.get(f"{base}/{result['id']}")).status_code == 401
    assert (
        await client.get(
            f"{ROLLOUT_PATH.format(revision_id=9999999)}/{result['id']}",
            headers=headers,
        )
    ).status_code == 404

    # A scalar lifecycle request shares the first slot. The untouched second
    # slot has no hidden queued operation.
    for id, expected in zip(ids, (409, 202), strict=True):
        scalar = await client.post(
            f"/admin/nodes/{id}/xray/instances/edge/start-operations",
            headers={**headers, "Idempotency-Key": str(uuid4())},
        )
        assert scalar.status_code == expected, scalar.text

    # Model an interrupted Worker after Stop with no durable Start result.
    operation_id = result["steps"][0]["operation"]["id"]
    container = cast(AsyncContainer, app.state.dishka_container)
    pipeline = await container.get(RestartRolloutPipeline)
    assert pg.db is not None
    engine = create_async_engine(pg.db.dsn)
    now = utc_now()
    try:
        async with engine.begin() as connection:
            await connection.execute(
                update(XrayStartTable)
                .where(col(XrayStartTable.id) == operation_id)
                .values(
                    state="running",
                    started_at=now,
                    stopped_at=now,
                    deadline_at=now + timedelta(seconds=45),
                )
            )
        retry = await pipeline.run(result["id"], operation_id)
        assert retry is not None and 0 < retry.seconds <= 45
        async with engine.begin() as connection:
            await connection.execute(
                update(XrayStartTable)
                .where(col(XrayStartTable.id) == operation_id)
                .values(
                    deadline_at=now - timedelta(seconds=1),
                )
            )
        assert await pipeline.run(result["id"], operation_id) is None
    finally:
        await engine.dispose()
    read = await client.get(f"{base}/{result['id']}", headers=headers)
    halted = read.json()["data"]
    assert (halted["state"], halted["reason"]) == ("halted", "target_unknown")
    assert [target["state"] for target in halted["steps"]] == [
        "unknown",
        "pending",
    ]
    assert halted["steps"][0]["operation"]["stopped_at"] is not None
    assert halted["steps"][0]["operation"]["reason"] == "dispatch_expired"
    assert halted["steps"][1]["operation"] is None

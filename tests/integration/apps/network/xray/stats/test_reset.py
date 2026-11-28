"""Exercise durable traffic reset admissions through the Panel."""

from asyncio import gather
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from ...nodes.auth import admin_headers

pytestmark = pytest.mark.integration


async def test_traffic_reset_admission(
    app: FastAPI, client: AsyncClient
) -> None:
    headers = await admin_headers(
        app, client, mobile="09120000775", role_key="xray-counter-reset"
    )
    created = await client.post(
        "/admin/nodes",
        headers=headers,
        json={"name": "Reset", "address": "reset.invalid", "port": 81},
    )
    assert created.status_code == 201, created.text
    node_id = created.json()["data"]["id"]
    base = f"/admin/nodes/{node_id}/xray/instances/edge/traffic"
    requests = {**headers, "Idempotency-Key": str(uuid4())}
    bad = await client.post(
        f"{base}/inbound/resets/scope",
        headers=requests,
        json={"max_counters": 1001, "confirm": True},
    )
    assert bad.status_code == 422, bad.text
    bad = await client.post(
        f"{base}/inbound/resets/scope",
        headers=requests,
        json={"max_counters": 10},
    )
    assert bad.status_code == 422, bad.text
    result, replay = await gather(
        *(
            client.post(
                f"{base}/outbound/resets/pair",
                headers=requests,
                json={"name": "direct"},
            )
            for _ in range(2)
        )
    )
    assert result.status_code == replay.status_code == 202, result.text
    operation = result.json()["data"]
    assert replay.json()["data"] == operation
    assert operation["state"] == "queued"
    read = await client.get(
        f"{base}/resets/{operation['id']}", headers=headers
    )
    assert read.json()["data"] == operation
    busy = await client.post(
        f"{base}/inbound/resets/counter",
        headers=requests,
        json={"name": "direct", "direction": "uplink"},
    )
    assert busy.status_code == 409, busy.text

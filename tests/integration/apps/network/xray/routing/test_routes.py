"""Exercise the Xray routing API and its tracked relative operations."""

from asyncio import gather
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from src.settings.config import CoreSettings

from ...nodes.auth import admin_headers

pytestmark = pytest.mark.integration


async def test_routing_admission_and_reads(
    app: FastAPI, client: AsyncClient
) -> None:
    headers = await admin_headers(
        app, client, mobile="09120000811", role_key="xray-routing"
    )
    node = await client.post(
        "/admin/nodes",
        headers=headers,
        json={
            "name": "Routing fixture",
            "address": "routing.invalid",
            "port": 81,
        },
    )
    assert node.status_code == 201, node.text
    node_id = node.json()["data"]["id"]
    base = f"/admin/nodes/{node_id}/xray/instances/edge/routing"
    for path in ("rules", "balancer?tag=pool"):
        reply = await client.get(f"{base}/{path}", headers=headers)
        assert reply.status_code == 200, reply.text
        assert reply.json()["data"]["status"] == "not_configured"
    test = await client.post(
        f"{base}/tests",
        headers=headers,
        json={"network": "tcp", "target_port": 443},
    )
    assert test.status_code == 200, test.text
    assert test.json()["data"]["status"] == "not_configured"
    for probe in (
        {"network": "icmp"},
        {"target_port": 65536},
        {"target_ip": "fe80::1%eth0"},
    ):
        reply = await client.post(f"{base}/tests", headers=headers, json=probe)
        assert reply.status_code == 422, reply.text

    run_headers = {**headers, "Idempotency-Key": str(uuid4())}
    rule = {"rule_json": '{"type":"field","network":"tcp","outboundTag":"a"}'}
    assert (
        await client.post(
            f"{base}/replacements", headers=run_headers, json=rule
        )
    ).status_code == 422
    assert (
        await client.post(
            f"{base}/replacements",
            headers=run_headers,
            json={**rule, "confirm_replace": 1},
        )
    ).status_code == 422
    first, replay = await gather(
        client.post(f"{base}/rules", headers=run_headers, json=rule),
        client.post(f"{base}/rules", headers=run_headers, json=rule),
    )
    assert first.status_code == replay.status_code == 202, first.text
    result = first.json()["data"]
    assert replay.json()["data"] == result
    assert result["state"] == "queued"
    assert "rule_json" not in first.text
    conflict = await client.delete(
        f"{base}/balancer-override",
        params={"tag": "pool"},
        headers=run_headers,
    )
    assert conflict.status_code == 409, conflict.text
    id = result["id"]
    assert (
        await client.get(f"{base}/operations/{id}", headers=headers)
    ).json()["data"] == result
    assert (
        await client.get(f"{base}/operations/{id}", headers={})
    ).status_code == 401


async def test_routing_mutation_requires_payload_protection(
    app: FastAPI, client: AsyncClient, pg: CoreSettings
) -> None:
    assert pg.crypto is not None
    pg.crypto.encryption_key = "replace-with-private-encryption-key"
    headers = await admin_headers(
        app, client, mobile="09120000813", role_key="xray-routing-protection"
    )
    response = await client.post(
        "/admin/nodes/1/xray/instances/edge/routing/rules",
        headers={**headers, "Idempotency-Key": str(uuid4())},
        json={"rule_json": '{"type":"field","outboundTag":"direct"}'},
    )
    assert response.status_code == 503, response.text
    assert response.json()["error"]["message_code"] == (
        "xray_routing_protection_unavailable"
    )

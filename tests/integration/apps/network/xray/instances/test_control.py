"""Track Xray Stop and restart without racing other lifecycle changes."""

from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from ...nodes.auth import admin_headers

pytestmark = pytest.mark.integration


async def test_stop_shares_one_slot_and_has_its_own_operation(
    app: FastAPI, client: AsyncClient
) -> None:
    headers = await admin_headers(
        app, client, mobile="09120000808", role_key="xray-control"
    )
    node = await client.post(
        "/admin/nodes",
        headers=headers,
        json={
            "name": "Xray control",
            "address": "control.invalid",
            "port": 81,
        },
    )
    assert node.status_code == 201, node.text
    base = f"/admin/nodes/{node.json()['data']['id']}/xray/instances/edge"
    revision = await client.post(
        "/admin/xray/revisions",
        headers=headers,
        json={"config_json": '{"remarks":"controlled restart"}'},
    )
    assert revision.status_code == 201, revision.text
    parent = f"{base}/config-revisions/{revision.json()['data']['id']}"
    stop_url = f"{base}/stop-operations"
    restart_url = f"{parent}/restart-operations"
    request = {**headers, "Idempotency-Key": str(uuid4())}
    accepted = await client.post(stop_url, headers=request)
    assert accepted.status_code == 202, accepted.text
    operation = accepted.json()["data"]
    assert operation["state"] == "queued"
    assert (await client.post(stop_url, headers=request)).json()["data"] == (
        operation
    )
    fresh = {**headers, "Idempotency-Key": str(uuid4())}
    for url in (
        restart_url,
        f"{parent}/apply-operations",
        f"{base}/start-operations",
    ):
        conflict = await client.post(url, headers=fresh)
        assert conflict.status_code == 409, conflict.text

    id = operation["id"]
    assert (await client.get(f"{stop_url}/{id}", headers=headers)).json()[
        "data"
    ] == (operation)
    assert (
        await client.get(f"{base}/start-operations/{id}", headers=headers)
    ).status_code == 404

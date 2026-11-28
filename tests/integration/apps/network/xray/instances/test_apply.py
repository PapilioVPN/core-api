"""Accept saved Xray revisions through the tracked instance lifecycle."""

from asyncio import gather
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from ...nodes.auth import admin_headers

pytestmark = pytest.mark.integration


async def test_apply_replays_and_shares_start_slot(
    app: FastAPI, client: AsyncClient
) -> None:
    headers = await admin_headers(
        app, client, mobile="09120000925", role_key="xray-apply-queue"
    )
    created = await client.post(
        "/admin/nodes",
        headers=headers,
        json={
            "name": "Xray apply queue",
            "address": "xray-apply.example.invalid",
            "port": 8081,
        },
    )
    assert created.status_code == 201, created.text
    revision_ids = []
    for source in ('{"remarks":"apply-a"}', '{"remarks":"apply-b"}'):
        revision = await client.post(
            "/admin/xray/revisions",
            headers=headers,
            json={"config_json": source},
        )
        assert revision.status_code == 201, revision.text
        revision_ids.append(revision.json()["data"]["id"])
    revision_id, other_revision = revision_ids
    node_id = created.json()["data"]["id"]
    instance = f"/admin/nodes/{node_id}/xray/instances/edge"
    start_url = f"{instance}/start-operations"
    target = f"{instance}/config-revisions"
    apply_url = f"{target}/{revision_id}/apply-operations"
    other_url = f"{target}/{other_revision}/apply-operations"
    run_headers = {**headers, "Idempotency-Key": str(uuid4())}
    assert (await client.post(apply_url, headers=headers)).status_code == 422
    assert (
        await client.post(
            f"{target}/99999999/apply-operations", headers=run_headers
        )
    ).status_code == 404

    first, repeated = await gather(
        client.post(apply_url, headers=run_headers),
        client.post(apply_url, headers=run_headers),
    )
    assert first.status_code == repeated.status_code == 202, first.text
    result = first.json()["data"]
    assert repeated.json()["data"] == result
    assert result["revision_id"] == revision_id
    assert result["state"] == "queued"
    assert (
        await client.post(other_url, headers=run_headers)
    ).status_code == 409
    for key in (run_headers["Idempotency-Key"], str(uuid4())):
        reply = await client.post(
            start_url, headers={**headers, "Idempotency-Key": key}
        )
        assert reply.status_code == 409, reply.text

    id = result["id"]
    observed = await client.get(f"{apply_url}/{id}", headers=headers)
    assert observed.json()["data"] == result
    for scope in (
        other_url,
        apply_url.replace("/edge/", "/other/"),
        start_url,
    ):
        assert (
            await client.get(f"{scope}/{id}", headers=headers)
        ).status_code == (404)

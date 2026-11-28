"""Verify that desired revision intent is independent of Node execution."""

from asyncio import gather
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from src.apps.network.nodes.registry.infra.pg.readers.endpoints import (
    NodeEndpointReader,
)
from src.apps.network.xray.assignments.infra.pg.readers.records import (
    XrayAssignmentReader,
)

from ...nodes.auth import admin_headers

pytestmark = pytest.mark.integration
ASSIGNMENT_PATH = (
    "/admin/nodes/{node_id}/xray/instances/{instance_id}/desired-revision"
)


async def test_desired_revision_upsert_clear_and_unavailable_observation(
    app: FastAPI,
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    batch_lookup = AsyncMock(
        side_effect=AssertionError("Scalar assignment used the endpoint set")
    )
    monkeypatch.setattr(NodeEndpointReader, "select_endpoints", batch_lookup)
    monkeypatch.setattr(XrayAssignmentReader, "select_desired", batch_lookup)
    path = ASSIGNMENT_PATH.format(node_id=999999, instance_id="edge")
    denied = await client.get(path)
    assert denied.status_code == 401, denied.text
    headers = await admin_headers(
        app, client, mobile="09120000765", role_key="xray-desired-records"
    )
    missing = await client.get(path, headers=headers)
    assert missing.status_code == 404, missing.text
    node = await client.post(
        "/admin/nodes",
        headers=headers,
        json={
            "name": "Desired revision",
            "address": "desired-revision.example.invalid",
            "port": 81,
        },
    )
    assert node.status_code == 201, node.text
    node_id = node.json()["data"]["id"]
    path = ASSIGNMENT_PATH.format(node_id=node_id, instance_id="edge")
    assigned = await client.get(path, headers=headers)
    assert assigned.status_code == 200, assigned.text
    assert assigned.json()["data"]["desired"] is None
    unassigned = (
        await client.get(f"{path}/comparison", headers=headers)
    ).json()["data"]
    assert (
        unassigned["state"] == "unassigned" and unassigned["observed"] is None
    )
    bad = await client.put(path, headers=headers, json={"revision_id": 999999})
    assert bad.status_code == 404, bad.text

    revisions = []
    for suffix in ("first", "second"):
        revision = await client.post(
            "/admin/xray/revisions",
            headers=headers,
            json={"config_json": f'{{"remarks":"desired-{suffix}"}}'},
        )
        assert revision.status_code == 201, revision.text
        revisions.append(revision.json()["data"])
    first, replay = await gather(
        *(
            client.put(
                path, headers=headers, json={"revision_id": revisions[0]["id"]}
            )
            for _ in range(2)
        )
    )
    assert first.status_code == replay.status_code == 200, first.text
    assert first.json()["data"] == replay.json()["data"]
    desired = first.json()["data"]["desired"]
    assert desired["revision_id"] == revisions[0]["id"]
    assert desired["config_sha256"] == revisions[0]["config_sha256"]
    compare = await client.get(f"{path}/comparison", headers=headers)
    assert compare.status_code == 200, compare.text
    view = compare.json()["data"]
    assert view["state"] == "unknown"
    assert view["observed"]["status"] == "not_configured"
    assert view["observed"]["received_at"] is None
    assert "no-store" in compare.headers["Cache-Control"]

    changed = await client.put(
        path, headers=headers, json={"revision_id": revisions[1]["id"]}
    )
    assert (
        changed.json()["data"]["desired"]["revision_id"] == revisions[1]["id"]
    )
    for _ in range(2):
        cleared = await client.delete(path, headers=headers)
        assert cleared.status_code == 204, cleared.text
    cleared = await client.get(path, headers=headers)
    assert cleared.json()["data"]["desired"] is None
    batch_lookup.assert_not_awaited()

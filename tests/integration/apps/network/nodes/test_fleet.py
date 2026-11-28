"""Exercise the Node picker, bulk state and fleet host API."""

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import event
from sqlalchemy.engine import Engine

from .auth import admin_headers

pytestmark = pytest.mark.integration


async def test_registry_selection_state_and_host_batch(
    app: FastAPI, client: AsyncClient
) -> None:
    headers = await admin_headers(
        app, client, mobile="09120000690", role_key="node-fleet"
    )

    async def create(label: str, enabled: bool) -> int:
        response = await client.post(
            "/admin/nodes",
            headers=headers,
            json={
                "name": f"Fleet registry {label}",
                "address": f"fleet-registry-{label}.example.invalid",
                "port": 81,
                "is_enabled": enabled,
            },
        )
        assert response.status_code == 201, response.text
        return response.json()["data"]["id"]

    disabled = await create("old", False)
    enabled = await create("new", True)
    first = await client.get(
        "/admin/nodes/simple",
        headers=headers,
        params={"q": "Fleet registry", "per_page": 1},
    )
    assert first.status_code == 200, first.text
    assert first.json()["data"] == [
        {"id": enabled, "name": "Fleet registry new", "is_enabled": True}
    ]
    assert first.json()["meta"]["next_before_id"] == enabled
    second = await client.get(
        "/admin/nodes/simple",
        headers=headers,
        params={"q": "Fleet registry", "per_page": 1, "before_id": enabled},
    )
    assert second.json()["data"] == [
        {"id": disabled, "name": "Fleet registry old", "is_enabled": False}
    ]
    assert second.json()["meta"]["next_before_id"] is None

    missing = 99999999
    selected = [disabled, enabled, missing, enabled]
    host_path = "/admin/nodes/host-stats"
    before = await client.post(
        host_path, headers=headers, json={"node_ids": selected}
    )
    assert before.status_code == 200, before.text
    assert [row["status"] for row in before.json()["data"]] == [
        "disabled",
        "not_configured",
        "node_not_found",
        "not_configured",
    ]
    assert [row["node_id"] for row in before.json()["data"]] == selected

    state_path = "/admin/nodes/state"
    changed = await client.patch(
        state_path,
        headers=headers,
        json={"node_ids": selected, "is_enabled": False},
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["data"] == [
        {"node_id": disabled, "status": "unchanged", "is_enabled": False},
        {"node_id": enabled, "status": "updated", "is_enabled": False},
        {"node_id": missing, "status": "node_not_found", "is_enabled": None},
    ]
    detail = await client.get(f"/admin/nodes/{enabled}", headers=headers)
    assert detail.json()["data"]["is_enabled"] is False
    assert detail.json()["data"]["connection_status"] == "unchecked"
    reenabled = await client.patch(
        state_path,
        headers=headers,
        json={"node_ids": [enabled], "is_enabled": True},
    )
    assert reenabled.json()["data"][0]["status"] == "updated"
    assert reenabled.json()["data"][0]["is_enabled"] is True

    fleet = [await create(f"set-{index}", True) for index in range(8)]
    commands: list[str] = []

    def observe_sql(
        _connection: object,
        _cursor: object,
        statement: str,
        _parameters: object,
        _context: object,
        _executemany: bool,
    ) -> None:
        sql = statement.strip().lower()
        if "tbl_nodes" in sql:
            commands.append(sql.split(None, 1)[0])

    event.listen(Engine, "before_cursor_execute", observe_sql)
    try:
        for ids in (fleet[:1], fleet[1:]):
            commands.clear()
            report = await client.post(
                host_path, headers=headers, json={"node_ids": ids}
            )
            assert report.status_code == 200, report.text
            assert commands == ["select"]
            commands.clear()
            report = await client.patch(
                state_path,
                headers=headers,
                json={"node_ids": ids, "is_enabled": False},
            )
            assert report.status_code == 200, report.text
            assert commands == ["select", "update"]
            assert all(
                row["status"] == "updated" for row in report.json()["data"]
            )
    finally:
        event.remove(Engine, "before_cursor_execute", observe_sql)

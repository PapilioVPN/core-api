"""Audit records follow committed administrator operations."""

from datetime import UTC, datetime, timedelta
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.infra.db.transaction import transaction

from src.apps.core.access.roles.app.interfaces.services import IRoleService
from src.apps.core.access.roles.domain.dtos.records import RoleCreate
from src.apps.core.access.users.app.interfaces.commands import (
    IUserCreateCommand,
    IUserRoleCommand,
)
from src.apps.core.access.users.domain.dtos.records import (
    UserCreate,
    UserRoleUpdate,
)

pytestmark = pytest.mark.integration


async def login(client: AsyncClient, mobile: str) -> dict[str, str]:
    response = await client.post(
        "/admin/auth/tokens",
        json={"mobile": mobile, "password": "isolated-audit-test-password"},
    )
    assert response.status_code == 200, response.text
    tokens: dict[str, str] = response.json()["data"]
    return tokens


def bearer(tokens: dict[str, str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def test_audit_records(app: FastAPI, client: AsyncClient) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        roles = await scope.get(IRoleService)
        original = await roles.create(
            RoleCreate(key="audit-original", title="Audit Original")
        )
        assigned = await roles.create(
            RoleCreate(key="audit-assigned", title="Audit Assigned")
        )
        users = await scope.get(IUserCreateCommand)
        admin = await users.create(
            UserCreate(
                first_name="Audit",
                last_name="Admin",
                mobile="09120000011",
                role_id=original.id,
                password="isolated-audit-test-password",
            ),
            super_admin=True,
        )
        viewer = await users.create(
            UserCreate(
                first_name="Audit",
                last_name="Viewer",
                mobile="09120000012",
                role_id=original.id,
                password="isolated-audit-test-password",
            )
        )

    url = "/admin/audit"
    headers = bearer(await login(client, admin.mobile))
    viewer_headers = bearer(await login(client, viewer.mobile))
    filters = {"actor_id": admin.id}
    assert (await client.get(url)).status_code == 401
    assert (await client.get(url, headers=viewer_headers)).status_code == 403
    empty = await client.get(url, headers=headers, params=filters)
    assert empty.status_code == 200, empty.text
    assert empty.json()["data"] == []
    since = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()

    changed = await client.patch(
        f"/admin/users/{viewer.id}/role",
        headers=headers,
        json={"role_id": assigned.id},
    )
    assert changed.status_code == 200, changed.text
    async with container() as scope:
        command = await scope.get(IUserRoleCommand)
        with pytest.raises(RuntimeError, match="intentional rollback"):
            async with transaction():
                await command.update(
                    viewer.id,
                    UserRoleUpdate(role_id=original.id),
                    actor_id=admin.id,
                )
                raise RuntimeError("intentional rollback")
    profile = await client.get("/admin/account/me", headers=viewer_headers)
    assert profile.json()["data"]["role_id"] == assigned.id

    created_scope = await client.post(
        "/admin/scopes",
        headers=headers,
        json={"key": "audit", "title": "Audit"},
    )
    assert created_scope.status_code == 201, created_scope.text
    scope_id = created_scope.json()["data"]["id"]
    grants = f"/admin/roles/{assigned.id}/scopes"
    added = await client.post(
        f"{grants}/batch",
        headers=headers,
        json={
            "items": [
                {"scope_id": scope_id, "permissions": 1},
                {"scope_id": scope_id, "permissions": 2},
            ]
        },
    )
    assert added.status_code == 200, added.text
    assert len(added.json()["data"]) == 1
    assert len(added.json()["errors"]) == 1
    assert (await client.get(url, headers=viewer_headers)).is_success
    updated = await client.patch(
        f"{grants}/batch",
        headers=headers,
        json={"items": [{"scope_id": scope_id, "permissions": 0}]},
    )
    assert updated.status_code == 200, updated.text
    assert (await client.get(url, headers=viewer_headers)).status_code == 403
    removed = await client.request(
        "DELETE", grants, headers=headers, json={"scope_id": scope_id}
    )
    assert removed.status_code == 200, removed.text

    sessions = "/admin/account/me/sessions"
    first = await client.get(sessions, headers=headers)
    assert first.status_code == 200, first.text
    current_id = first.json()["data"][0]["id"]
    foreign = await client.delete(
        f"{sessions}/{current_id}", headers=viewer_headers
    )
    assert foreign.status_code == 404
    other = bearer(await login(client, admin.mobile))
    assert (
        await client.delete(f"{sessions}/{current_id}", headers=other)
    ).is_success
    assert (
        await client.delete(f"{sessions}/{current_id}", headers=other)
    ).status_code == 404
    logged_out = await login(client, admin.mobile)
    payload = {"refresh_token": logged_out["refresh_token"]}
    endpoint = "/admin/auth/refresh-tokens"
    for _ in range(2):
        assert (
            await client.request("DELETE", endpoint, json=payload)
        ).is_success
    assert (
        await client.get(sessions, headers=bearer(logged_out))
    ).status_code == 401
    await login(client, admin.mobile)
    assert (await client.delete(sessions, headers=other)).json()["data"][
        "count"
    ] == 1
    assert (await client.delete(sessions, headers=other)).json()["data"][
        "count"
    ] == 0

    page = await client.get(
        url, headers=other, params={**filters, "per_page": 2}
    )
    assert page.status_code == 200, page.text
    meta = page.json()["meta"]
    assert meta["pager"]["total_items"] == 7
    assert meta["pager"]["has_next"] is True
    assert {option["value"] for option in meta["sorts"]["options"]} == {
        "created_at",
        "id",
    }
    available = {item["key"]: item for item in meta["filters"]}
    assert available["actor_id"]["type"] == "checkbox"
    assert {"id": admin.id, "label": f"#{admin.id}", "count": 7} in (
        available["actor_id"]["options"]
    )
    assert available["created_at"]["type"] == "slider"
    assert (
        available["created_at"]["minimum"]
        <= available["created_at"]["maximum"]
    )
    actions = await client.get(
        url, headers=other, params={**filters, "since": since}
    )
    rows = actions.json()["data"]
    assert [row["action"] for row in rows] == [
        "session.revoke_others",
        "session.revoke",
        "session.revoke",
        "role.scope.remove",
        "role.scope.update",
        "role.scope.create",
        "user.role.update",
    ]
    assert all(row["actor_id"] == admin.id for row in rows)
    assert rows[0]["count"] == 1
    assert rows[2]["target_id"] == current_id
    assert rows[4]["permissions"] == 0
    assert rows[4]["scope_id"] == scope_id
    assert rows[6]["target_id"] == str(viewer.id)
    assert rows[6]["role_id"] == assigned.id
    filtered = await client.get(
        url, headers=other, params={**filters, "action": "user.role.update"}
    )
    assert filtered.json()["data"] == [rows[6]]
    filtered_options = {
        item["key"]: item for item in filtered.json()["meta"]["filters"]
    }
    assert filtered_options["action"] == available["action"]
    searched = await client.get(
        url, headers=other, params={**filters, "q": "SESSION", "per_page": 1}
    )
    found = searched.json()
    assert found["meta"]["pager"]["total_items"] == 3
    assert len(found["data"]) == 1
    options = {item["key"]: item for item in found["meta"]["filters"]}
    counts = {
        option["id"]: option["count"]
        for option in options["action"]["options"]
    }
    assert counts["session.revoke"] >= 2
    assert counts["session.revoke_others"] >= 1
    assert {"id": admin.id, "label": f"#{admin.id}", "count": 3} in (
        options["actor_id"]["options"]
    )
    sorted_page = await client.get(
        url,
        headers=other,
        params=[
            ("actor_id", str(admin.id)),
            ("actor_id", str(viewer.id)),
            ("action", "session.revoke"),
            ("action", "user.role.update"),
            ("sort_by", "id"),
            ("sort_order", "asc"),
        ],
    )
    assert sorted_page.json()["data"] == [rows[6], rows[2], rows[1]]
    assert (
        options["created_at"]["minimum"] >= available["created_at"]["minimum"]
    )
    exact = await client.get(
        url,
        headers=other,
        params={
            "q": current_id,
            "since": available["created_at"]["minimum"],
            "until": available["created_at"]["maximum"],
        },
    )
    assert exact.json()["data"] == [rows[2]]
    percent = await client.get(url, headers=other, params={"q": "%"})
    assert percent.json()["data"] == []
    bounds = await client.get(
        url, headers=other, params={**filters, "until": since}
    )
    assert bounds.json()["data"] == []
    invalid = await client.get(
        url, headers=other, params={"since": since, "until": since}
    )
    assert invalid.status_code == 400
    assert invalid.json()["error"]["message_code"] == "invalid_audit_range"

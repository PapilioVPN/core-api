"""Exercise native administrator operations against the migrated schema."""

from asyncio import gather
from datetime import UTC, datetime, timedelta
from os import getpid
from typing import cast
from uuid import uuid4

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.errors.exceptions import ConflictException

from src.apps.core.auth.app.services.sessions import SessionService
from src.apps.core.tokens.app.interfaces.services import ITokenService
from src.apps.core.tokens.domain.models.tokens import TokenIdentity
from src.apps.core.users.app.commands.owner import OwnerCommand
from src.apps.core.users.domain.dtos.owner import OwnerCreate

pytestmark = pytest.mark.integration


async def test_core_access(app: FastAPI, client: AsyncClient) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    owner = OwnerCreate(
        first_name="Test",
        last_name="Owner",
        mobile="09120000001",
        password="owner-password-for-test",
    )
    async with container() as scope:
        await (await scope.get(OwnerCommand)).create(owner)
    async with container() as scope:
        with pytest.raises(ConflictException):
            await (await scope.get(OwnerCommand)).create(owner)

    assert (
        await client.get("/admin/health/resources/memory")
    ).status_code == 401
    rejected = await client.post(
        "/admin/auth/tokens",
        json={"mobile": owner.mobile, "password": "incorrect-password"},
    )
    assert rejected.status_code == 401
    invalid = await client.post(
        "/admin/auth/tokens", json={"password": "hidden"}
    )
    assert invalid.status_code == 422
    assert "hidden" not in invalid.text
    assert invalid.json()["errors"][0]["loc"] == ["mobile"]
    invalid_refresh = await client.post(
        "/admin/auth/refresh-tokens",
        json={"refresh_token": ["hidden-refresh"]},
    )
    assert invalid_refresh.status_code == 422
    assert "hidden-refresh" not in invalid_refresh.text
    assert invalid_refresh.json()["errors"][0]["loc"] == ["refresh_token"]
    login = await client.post(
        "/admin/auth/tokens",
        json={"mobile": owner.mobile, "password": owner.password},
    )
    assert login.status_code == 200, login.text
    tokens = login.json()["data"]
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    me = await client.get("/admin/account/me", headers=headers)
    assert me.status_code == 200, me.text
    profile = me.json()["data"]
    assert profile["is_super_admin"] is True
    assert profile["scopes"] == {"access": 15, "system": 1}
    scope_list = await client.get("/admin/scopes", headers=headers)
    system_scope = next(
        item for item in scope_list.json()["data"] if item["key"] == "system"
    )
    reduced = await client.request(
        "DELETE",
        f"/admin/roles/{profile['role_id']}/scopes",
        json={"scope_id": system_scope["id"]},
        headers=headers,
    )
    assert reduced.status_code == 200, reduced.text
    first_tokens = tokens
    first_headers = headers
    relogin = await client.post(
        "/admin/auth/tokens",
        json={"mobile": owner.mobile, "password": owner.password},
        headers={"User-Agent": "Papilio Panel Test"},
    )
    assert relogin.status_code == 200
    tokens = relogin.json()["data"]
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    me = await client.get("/admin/account/me", headers=headers)
    assert me.json()["data"]["scopes"] == {"access": 15}
    assert (
        await client.delete(f"/admin/users/{profile['id']}", headers=headers)
    ).status_code == 403

    for path in (
        "/admin/health/postgres",
        "/admin/health/postgres/time",
        "/admin/health/redis",
        "/admin/health/resources/host",
        "/admin/health/resources/runtime",
        "/admin/health/resources/sessions",
        "/admin/health/resources/cpu",
        "/admin/health/resources/cpu/usage?sample_seconds=0.02",
        "/admin/health/resources/cpu/cores/usage?sample_seconds=0.02",
        "/admin/health/resources/memory",
        "/admin/health/resources/swap",
        "/admin/health/network/interfaces",
        "/admin/health/network/io",
        "/admin/health/network/io/total",
        "/admin/health/storage/partitions",
        "/admin/health/storage/usage?path=/",
        "/admin/health/storage/io",
        "/admin/health/storage/io/total",
        "/admin/health/processes?limit=2",
        "/admin/health/processes/count",
        f"/admin/health/processes/{getpid()}",
        "/admin/health/sensors/temperatures",
        "/admin/health/sensors/fans",
        "/admin/health/sensors/battery",
    ):
        response = await client.get(path, headers=headers)
        assert response.status_code == 200, (path, response.text)
        assert response.json()["data"]["duration_ms"] >= 0

    new_scope = await client.post(
        "/admin/scopes",
        json={"key": "reports", "title": "Reports"},
        headers=headers,
    )
    assert new_scope.status_code == 201, new_scope.text
    scope_id = new_scope.json()["data"]["id"]
    new_role = await client.post(
        "/admin/roles",
        json={"key": "viewer", "title": "Viewer"},
        headers=headers,
    )
    assert new_role.status_code == 201, new_role.text
    role_id = new_role.json()["data"]["id"]

    grants = f"/admin/roles/{role_id}/scopes"
    assigned = await client.post(
        grants,
        json={"scope_id": scope_id, "permissions": 1},
        headers=headers,
    )
    assert assigned.status_code == 201, assigned.text
    changed = await client.patch(
        grants,
        json={"scope_id": scope_id, "permissions": 0},
        headers=headers,
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["data"]["permissions"] == 0
    batch = await client.patch(
        f"{grants}/batch",
        json={"items": [{"scope_id": scope_id, "permissions": 1}]},
        headers=headers,
    )
    assert batch.status_code == 200, batch.text
    assert batch.json()["data"][0]["permissions"] == 1

    user = await client.post(
        "/admin/users",
        json={
            "first_name": "Test",
            "last_name": "Viewer",
            "mobile": "09120000002",
            "password": "viewer-password-for-test",
            "role_id": role_id,
            "is_super_admin": True,
        },
        headers=headers,
    )
    assert user.status_code == 201, user.text
    assert "hashed_password" not in user.json()["data"]
    assert user.json()["data"]["is_super_admin"] is False
    user_id = user.json()["data"]["id"]
    updated = await client.patch(
        f"/admin/users/{user_id}",
        json={"first_name": "Other"},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    found = await client.get("/admin/users?q=09120000002", headers=headers)
    assert found.json()["data"][0]["first_name"] == "Other"

    viewer = await client.post(
        "/admin/auth/tokens",
        json={"mobile": "09120000002", "password": "viewer-password-for-test"},
    )
    assert viewer.status_code == 200, viewer.text
    viewer_headers = {
        "Authorization": f"Bearer {viewer.json()['data']['access_token']}"
    }
    denied = await client.get(
        "/admin/health/resources/memory", headers=viewer_headers
    )
    assert denied.status_code == 403
    system_grant = {"scope_id": system_scope["id"], "permissions": 1}
    assert (
        await client.post(grants, json=system_grant, headers=headers)
    ).status_code == 201
    assert (
        await client.get(
            "/admin/health/resources/memory", headers=viewer_headers
        )
    ).status_code == 200
    assert (
        await client.patch(
            grants, json={**system_grant, "permissions": 0}, headers=headers
        )
    ).status_code == 200
    assert (
        await client.get(
            "/admin/health/resources/memory", headers=viewer_headers
        )
    ).status_code == 403

    password_url = "/admin/account/me/password"
    new_password = "updated-viewer-password"
    bad_password = await client.patch(
        password_url,
        json={
            "current_password": "incorrect-password",
            "password": new_password,
        },
        headers=viewer_headers,
    )
    assert bad_password.status_code == 401
    changed_password = await client.patch(
        password_url,
        json={
            "current_password": "viewer-password-for-test",
            "password": new_password,
        },
        headers=viewer_headers,
    )
    assert changed_password.status_code == 200, changed_password.text
    changed_login = await client.post(
        "/admin/auth/tokens",
        json={"mobile": "09120000002", "password": new_password},
    )
    assert changed_login.status_code == 200

    refresh_url = "/admin/auth/refresh-tokens"
    sessions_url = "/admin/account/me/sessions"
    changed_tokens = changed_login.json()["data"]
    assert (
        await client.request(
            "DELETE",
            refresh_url,
            json={"refresh_token": changed_tokens["refresh_token"]},
        )
    ).status_code == 200
    assert (
        await client.get(
            sessions_url,
            headers={
                "Authorization": f"Bearer {changed_tokens['access_token']}"
            },
        )
    ).status_code == 401
    assert (await client.get(sessions_url, headers=viewer_headers)).is_success

    async with container() as scope:
        service = await scope.get(SessionService)
        await service.create(
            profile["id"],
            uuid4(),
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
            user_agent=None,
        )
        legacy = await (await scope.get(ITokenService)).issue(
            TokenIdentity(
                subject=str(profile["id"]),
                audience="admin",
                claims={
                    "role_id": profile["role_id"],
                    "scopes": {"access": 15},
                },
            )
        )
    assert (
        await client.get(
            sessions_url,
            headers={"Authorization": f"Bearer {legacy.access_token}"},
        )
    ).status_code == 401
    assert (
        await client.post(
            refresh_url, json={"refresh_token": legacy.refresh_token}
        )
    ).status_code == 401
    sessions = await client.get(sessions_url, headers=headers)
    assert sessions.status_code == 200, sessions.text
    current = next(item for item in sessions.json()["data"] if item["current"])
    assert current["created_at"] <= current["last_seen_at"]
    assert current["user_agent"] == "Papilio Panel Test"
    assert "refresh_token" not in current
    page = await client.get(f"{sessions_url}?per_page=1", headers=headers)
    assert len(page.json()["data"]) == 1
    assert page.json()["meta"]["total_items"] == 2
    async with container() as scope:
        service = await scope.get(SessionService)
        assert await service.remove_expired(limit=100) == 1
        assert await service.remove_expired(limit=100) == 0
    current_url = f"{sessions_url}/{current['id']}"
    assert (
        await client.delete(current_url, headers=viewer_headers)
    ).status_code == 404

    refreshes = await gather(
        *[
            client.post(
                refresh_url, json={"refresh_token": tokens["refresh_token"]}
            )
            for _ in range(2)
        ]
    )
    assert sorted(response.status_code for response in refreshes) == [200, 401]
    refresh = next(response for response in refreshes if response.is_success)
    rotated = refresh.json()["data"]
    rotated_headers = {"Authorization": f"Bearer {rotated['access_token']}"}
    page = await client.get(sessions_url, headers=rotated_headers)
    assert [item["id"] for item in page.json()["data"] if item["current"]] == [
        current["id"]
    ]
    assert len(page.json()["data"]) == 2
    other = next(item for item in page.json()["data"] if not item["current"])
    closed = await client.delete(sessions_url, headers=rotated_headers)
    assert closed.status_code == 200, closed.text
    assert closed.json()["data"]["count"] == 1
    assert (
        await client.get(sessions_url, headers=first_headers)
    ).status_code == 401
    assert (
        await client.post(
            refresh_url, json={"refresh_token": first_tokens["refresh_token"]}
        )
    ).status_code == 401
    page = await client.get(sessions_url, headers=rotated_headers)
    assert [item["id"] for item in page.json()["data"]] == [current["id"]]
    assert (
        await client.delete(
            f"{sessions_url}/{other['id']}", headers=rotated_headers
        )
    ).status_code == 404
    replay = await client.post(
        refresh_url,
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert replay.status_code == 401
    fresh = {"refresh_token": rotated["refresh_token"]}
    await client.request(
        "DELETE", refresh_url, json={"refresh_token": tokens["refresh_token"]}
    )
    assert (await client.get(sessions_url, headers=rotated_headers)).is_success
    assert (
        await client.delete(current_url, headers=rotated_headers)
    ).is_success
    assert (
        await client.get(sessions_url, headers=rotated_headers)
    ).status_code == 401
    assert (
        await client.get("/admin/account/me", headers=headers)
    ).status_code == 401
    assert (
        await client.request("DELETE", refresh_url, json=fresh)
    ).status_code == 200
    assert (await client.post(refresh_url, json=fresh)).status_code == 401

    login = await client.post(
        "/admin/auth/tokens",
        json={"mobile": owner.mobile, "password": owner.password},
    )
    headers = {
        "Authorization": f"Bearer {login.json()['data']['access_token']}"
    }
    removed = await client.delete(f"/admin/users/{user_id}", headers=headers)
    assert removed.status_code == 200, removed.text
    removed = await client.delete(f"/admin/roles/{role_id}", headers=headers)
    assert removed.status_code == 200, removed.text
    removed = await client.delete(f"/admin/scopes/{scope_id}", headers=headers)
    assert removed.status_code == 200, removed.text

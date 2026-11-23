"""Manage shared shop services through the native administrator API."""

from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient

from src.apps.core.auth.domain.enums.permissions import AdminPermission
from src.apps.core.roles.app.interfaces.services import IRoleService
from src.apps.core.roles.domain.dtos.records import RoleCreate
from src.apps.core.users.app.interfaces.commands import IUserCreateCommand
from src.apps.core.users.domain.dtos.records import UserCreate

pytestmark = pytest.mark.integration

PASSWORD = "isolated-shop-services-test-password"


async def login(client: AsyncClient, mobile: str) -> dict[str, str]:
    response = await client.post(
        "/admin/auth/tokens", json={"mobile": mobile, "password": PASSWORD}
    )
    assert response.status_code == 200, response.text
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_services(app: FastAPI, client: AsyncClient) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.create(
            RoleCreate(key="shop-operator", title="Shop Operator")
        )
        users = await scope.get(IUserCreateCommand)
        admin = await users.create(
            UserCreate(
                first_name="Shop",
                last_name="Admin",
                mobile="09120000041",
                role_id=role.id,
                password=PASSWORD,
            ),
            super_admin=True,
        )
        operator = await users.create(
            UserCreate(
                first_name="Shop",
                last_name="Operator",
                mobile="09120000042",
                role_id=role.id,
                password=PASSWORD,
            )
        )

    url = "/admin/services"
    assert (await client.get(url)).status_code == 401
    headers = await login(client, admin.mobile)
    operator_headers = await login(client, operator.mobile)
    assert (await client.get(url, headers=operator_headers)).status_code == 403

    created = await client.post(
        url,
        headers=headers,
        json={
            "title": "VIP",
            "description": "Multiple locations",
            "priority": 10,
        },
    )
    assert created.status_code == 201, created.text
    vip = created.json()["data"]
    assert vip["is_active"] is True
    path = f"{url}/{vip['id']}"

    shop = await client.post(
        "/admin/scopes", headers=headers, json={"key": "shop", "title": "Shop"}
    )
    assert shop.status_code == 201, shop.text
    scope_id = shop.json()["data"]["id"]
    grants = f"/admin/roles/{role.id}/scopes/batch"
    grant = await client.post(
        grants,
        headers=headers,
        json={
            "items": [
                {"scope_id": scope_id, "permissions": AdminPermission.READ}
            ]
        },
    )
    assert grant.status_code == 200, grant.text
    shared = await client.get(path, headers=operator_headers)
    assert shared.status_code == 200, shared.text
    assert shared.json()["data"] == vip
    forbidden = await client.patch(
        path, headers=operator_headers, json={"is_active": False}
    )
    assert forbidden.status_code == 403, forbidden.text

    created = await client.post(
        url, headers=headers, json={"title": "Economy"}
    )
    assert created.status_code == 201, created.text
    page = await client.get(url, headers=headers, params={"per_page": 1})
    assert page.status_code == 200, page.text
    assert page.json()["data"][0]["title"] == "Economy"
    assert page.json()["meta"]["total_items"] == 2

    paused = await client.patch(
        path, headers=headers, json={"is_active": False, "description": None}
    )
    assert paused.status_code == 200, paused.text
    row = paused.json()["data"]
    assert row["description"] is None
    assert row["is_active"] is False
    assert row["id"] == vip["id"] and row["priority"] == 10
    page = await client.get(
        url, headers=operator_headers, params={"is_active": False, "q": "vip"}
    )
    assert page.status_code == 200, page.text
    assert page.json()["data"] == [row]

    invalid = await client.patch(path, headers=headers, json={"title": None})
    assert invalid.status_code == 422, invalid.text
    missing = await client.get(f"{url}/99999", headers=headers)
    assert missing.status_code == 404, missing.text

"""Exercise reusable volume definitions through the administrator API."""

from asyncio import gather
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient

from src.apps.core.roles.app.interfaces.services import IRoleService
from src.apps.core.roles.domain.dtos.records import RoleCreate
from src.apps.core.users.app.interfaces.commands import IUserCreateCommand
from src.apps.core.users.domain.dtos.records import UserCreate

pytestmark = pytest.mark.integration


async def test_volumes(app: FastAPI, client: AsyncClient) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    password = "isolated-shop-volumes-test-password"
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.create(
            RoleCreate(key="volumes-admin", title="Volumes Admin")
        )
        users = await scope.get(IUserCreateCommand)
        admin = await users.create(
            UserCreate(
                first_name="Volume",
                last_name="Admin",
                mobile="09120000043",
                role_id=role.id,
                password=password,
            ),
            super_admin=True,
        )

    url = "/admin/volumes"
    assert (await client.get(url)).status_code == 401
    login = await client.post(
        "/admin/auth/tokens",
        json={"mobile": admin.mobile, "password": password},
    )
    assert login.status_code == 200, login.text
    headers = {
        "Authorization": f"Bearer {login.json()['data']['access_token']}"
    }
    fixed = {"size_bytes": 50 * 1024**3}
    created, repeated = await gather(
        client.post(url, json=fixed, headers=headers),
        client.post(url, json=fixed, headers=headers),
    )
    assert created.status_code == 201, created.text
    assert repeated.status_code == 201, repeated.text
    row = created.json()["data"]
    assert repeated.json()["data"] == row
    assert row["size_bytes"] == fixed["size_bytes"]
    path = f"{url}/{row['id']}"

    custom = {
        "mode": "custom",
        "min_bytes": 10 * 1024**3,
        "max_bytes": 100 * 1024**3,
        "step_bytes": 5 * 1024**3,
    }
    page = await client.get(
        url,
        headers=headers,
        params=fixed,
    )
    assert page.status_code == 200, page.text
    assert page.json()["meta"]["total_items"] == 1
    assert page.json()["data"] == [row]
    invalid = await client.post(url, headers=headers, json=custom)
    assert invalid.status_code == 422, invalid.text
    invalid = await client.post(
        url, headers=headers, json={**fixed, "size_bytes": 2**63}
    )
    assert invalid.status_code == 422, invalid.text

    change = await client.patch(path, json={"size_bytes": 1}, headers=headers)
    assert change.status_code == 405, change.text
    stored = await client.get(path, headers=headers)
    assert stored.status_code == 200, stored.text
    assert stored.json()["data"]["size_bytes"] == fixed["size_bytes"]

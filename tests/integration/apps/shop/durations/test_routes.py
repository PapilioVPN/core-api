"""Exercise reusable duration definitions through the administrator API."""

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


async def test_durations(app: FastAPI, client: AsyncClient) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    password = "isolated-shop-durations-test-password"
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.create(
            RoleCreate(key="durations-admin", title="Durations Admin")
        )
        users = await scope.get(IUserCreateCommand)
        admin = await users.create(
            UserCreate(
                first_name="Duration",
                last_name="Admin",
                mobile="09120000044",
                role_id=role.id,
                password=password,
            ),
            super_admin=True,
        )

    url = "/admin/durations"
    assert (await client.get(url)).status_code == 401
    login = await client.post(
        "/admin/auth/tokens",
        json={"mobile": admin.mobile, "password": password},
    )
    assert login.status_code == 200, login.text
    headers = {
        "Authorization": f"Bearer {login.json()['data']['access_token']}"
    }

    created = await client.post(url, json={"days": 30}, headers=headers)
    assert created.status_code == 201, created.text
    first = created.json()["data"]
    assert first["days"] == 30 and first["starts_on"] == "ready"
    path = f"{url}/{first['id']}"
    repeated = await client.post(
        url, json={"days": 30, "starts_on": "ready"}, headers=headers
    )
    assert repeated.status_code == 201, repeated.text
    assert repeated.json()["data"] == first

    created = await client.post(
        url, json={"days": 45, "starts_on": "ready"}, headers=headers
    )
    assert created.status_code == 201, created.text
    second = created.json()["data"]
    assert second["id"] != first["id"] and second["days"] == 45

    response = await client.get(
        url, params={"page": 2, "per_page": 1}, headers=headers
    )
    assert response.status_code == 200, response.text
    assert response.json()["data"] == [second]
    assert response.json()["meta"]["total_items"] == 2

    for data in (
        {"days": 0},
        {"days": 2**31},
        {"days": 30, "starts_on": "typo"},
    ):
        invalid = await client.post(url, json=data, headers=headers)
        assert invalid.status_code == 422, invalid.text

    change = await client.patch(path, json={"days": 90}, headers=headers)
    assert change.status_code == 405, change.text
    stored = await client.get(path, headers=headers)
    assert stored.status_code == 200, stored.text
    assert stored.json()["data"] == first

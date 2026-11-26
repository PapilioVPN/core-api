"""Create isolated operator credentials for node integration tests."""

from typing import cast

from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient

from src.apps.core.access.roles.app.interfaces.services import IRoleService
from src.apps.core.access.roles.domain.dtos.records import RoleCreate
from src.apps.core.access.users.app.interfaces.commands import (
    IUserCreateCommand,
)
from src.apps.core.access.users.domain.dtos.records import UserCreate


async def admin_headers(
    app: FastAPI,
    client: AsyncClient,
    *,
    mobile: str = "09120000916",
    role_key: str = "host-test",
) -> dict[str, str]:
    container = cast(AsyncContainer, app.state.dishka_container)
    password = "isolated-host-stats-test-password"
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.create(RoleCreate(key=role_key, title="Host Test"))
        users = await scope.get(IUserCreateCommand)
        admin = await users.create(
            UserCreate(
                first_name="Host",
                last_name="Operator",
                mobile=mobile,
                role_id=role.id,
                password=password,
            ),
            super_admin=True,
        )
    login = await client.post(
        "/admin/auth/tokens",
        json={"mobile": admin.mobile, "password": password},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['data']['access_token']}"}

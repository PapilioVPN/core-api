"""Operator access for customer panel checks."""

from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient

from src.apps.core.access.roles.app.interfaces.services import IRoleService
from src.apps.core.access.roles.domain.dtos.records import RoleCreate
from src.apps.core.access.users.app.interfaces.commands import (
    IUserCreateCommand,
)
from src.apps.core.access.users.domain.dtos.records import UserCreate


@pytest.fixture
async def admin(
    app: FastAPI, client: AsyncClient, request: pytest.FixtureRequest
) -> dict[str, str]:
    number, super_admin = request.param
    password = "isolated-customer-panel-test-password"
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.create(
            RoleCreate(
                key=f"customer-test-{number}", title="Customer Operator"
            )
        )
        users = await scope.get(IUserCreateCommand)
        user = await users.create(
            UserCreate(
                first_name="Test",
                last_name="Operator",
                role_id=role.id,
                mobile=f"09120000{number}",
                password=password,
            ),
            super_admin=super_admin,
        )
    response = await client.post(
        "/admin/auth/tokens",
        json={"mobile": user.mobile, "password": password},
    )
    assert response.status_code == 200
    return {
        "Authorization": f"Bearer {response.json()['data']['access_token']}"
    }

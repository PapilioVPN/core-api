"""Register and read top-up requests through the administrator API."""

from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.types.constants import INT64_MAX

from src.apps.core.access.roles.app.interfaces.services import IRoleService
from src.apps.core.access.roles.domain.dtos.records import RoleCreate
from src.apps.core.access.users.app.interfaces.commands import (
    IUserCreateCommand,
)
from src.apps.core.access.users.domain.dtos.records import UserCreate
from src.apps.shop.wallets.balance.app.interfaces.services import (
    IWalletBalanceService,
)

pytestmark = pytest.mark.integration


async def _headers(
    app: FastAPI, client: AsyncClient, *, super_admin: bool
) -> dict[str, str]:
    container = cast(AsyncContainer, app.state.dishka_container)
    suffix = 1 if super_admin else 2
    mobile = f"0917800480{suffix}"
    password = "isolated-wallet-deposits-password"
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.create(
            RoleCreate(key=f"wallet-deposits-{suffix}", title="Deposit Test")
        )
        users = await scope.get(IUserCreateCommand)
        await users.create(
            UserCreate(
                first_name="Deposit",
                last_name="Operator",
                mobile=mobile,
                password=password,
                role_id=role.id,
            ),
            super_admin=super_admin,
        )
    response = await client.post(
        "/admin/auth/tokens", json={"mobile": mobile, "password": password}
    )
    assert response.status_code == 200, response.text
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _customer(client: AsyncClient, headers: dict[str, str]) -> int:
    response = await client.post(
        "/admin/customers", headers=headers, json={"name": "Top-up Customer"}
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]["id"]


async def test_create_and_read_deposits(
    app: FastAPI, client: AsyncClient
) -> None:
    admin = await _headers(app, client, super_admin=True)
    customer_id = await _customer(client, admin)
    other_id = await _customer(client, admin)
    path = f"/admin/wallets/{customer_id}/deposits"
    other_path = f"/admin/wallets/{other_id}/deposits"

    for amount in (0, -1, "100", True, INT64_MAX + 1):
        invalid = await client.post(
            path, headers=admin, json={"amount": amount}
        )
        assert invalid.status_code == 422, invalid.text
    missing = await client.post(
        f"/admin/wallets/{INT64_MAX}/deposits",
        headers=admin,
        json={"amount": 1},
    )
    assert missing.status_code == 404, missing.text

    created = await client.post(
        path,
        headers=admin,
        json={"amount": INT64_MAX, "customer_id": other_id},
    )
    assert created.status_code == 201, created.text
    first = created.json()["data"]
    assert first["customer_id"] == customer_id
    assert first["amount"] == INT64_MAX
    assert first["created_at"]

    created = await client.post(path, headers=admin, json={"amount": 500})
    assert created.status_code == 201, created.text
    second = created.json()["data"]
    detail = await client.get(f"{path}/{first['id']}", headers=admin)
    assert detail.status_code == 200, detail.text
    assert detail.json()["data"] == first
    assert (
        await client.get(f"{other_path}/{first['id']}", headers=admin)
    ).status_code == 404

    listed = await client.get(path, headers=admin, params={"per_page": 1})
    assert listed.status_code == 200, listed.text
    assert listed.json()["data"] == [second]
    assert listed.json()["meta"]["total_items"] == 2
    assert listed.json()["meta"]["has_next"] is True
    filtered = await client.get(
        path, headers=admin, params={"amount": INT64_MAX}
    )
    assert filtered.status_code == 200, filtered.text
    assert filtered.json()["data"] == [first]
    assert (await client.get(other_path, headers=admin)).json()["data"] == []

    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        balances = await scope.get(IWalletBalanceService)
        assert await balances.find(customer_id) is None


async def test_deposits_require_shop_access(
    app: FastAPI, client: AsyncClient
) -> None:
    path = "/admin/wallets/1/deposits"
    assert (await client.get(path)).status_code == 401
    assert (await client.post(path, json={"amount": 1})).status_code == 401
    headers = await _headers(app, client, super_admin=False)
    assert (await client.get(path, headers=headers)).status_code == 403
    forbidden = await client.post(path, headers=headers, json={"amount": 1})
    assert forbidden.status_code == 403

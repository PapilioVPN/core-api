"""Issue and read expiring top-up invoices through the panel."""

from datetime import datetime, timedelta
from os import environ
from typing import cast
from uuid import UUID

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.infra.redis.client import RedisClient, resolve
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
from src.apps.shop.wallets.deposits.routers.schemas import records

pytestmark = pytest.mark.integration


async def _headers(
    app: FastAPI, client: AsyncClient, *, super_admin: bool, suffix: int = 1
) -> dict[str, str]:
    container = cast(AsyncContainer, app.state.dishka_container)
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


@pytest.mark.skipif(
    not environ.get("PAPILIOVPN_TEST_REDIS_URL"),
    reason="Set PAPILIOVPN_TEST_REDIS_URL to the isolated test Redis",
)
async def test_issue_and_read_invoice(
    app: FastAPI, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
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
    assert UUID(first["id"]).version == 4
    expires = datetime.fromisoformat(first["expires_at"])
    started = datetime.fromisoformat(first["created_at"])
    assert (expires - started).total_seconds() == 3600
    assert 0 < first.pop("expires_in") <= 3600

    created = await client.post(path, headers=admin, json={"amount": 500})
    assert created.status_code == 201, created.text
    second = created.json()["data"]
    with monkeypatch.context() as clock:
        clock.setattr(
            records, "utc_now", lambda: started + timedelta(seconds=30)
        )
        detail = await client.get(f"{path}/{first['id']}", headers=admin)
    assert detail.status_code == 200, detail.text
    result = detail.json()["data"]
    assert result.pop("expires_in") == 3570
    assert result == first
    assert (
        await client.get(f"{other_path}/{first['id']}", headers=admin)
    ).status_code == 404

    container = cast(AsyncContainer, app.state.dishka_container)
    redis = await container.get(RedisClient)
    key = f"shop:wallets:deposits:{customer_id}"
    assert await resolve(redis.client.hexpiretime(key, first["id"])) == [
        int(expires.timestamp())
    ]
    await resolve(redis.client.hexpire(key, 0, first["id"]))
    expired = await client.get(f"{path}/{first['id']}", headers=admin)
    assert expired.status_code == 404, expired.text
    remaining = await client.get(f"{path}/{second['id']}", headers=admin)
    result = remaining.json()["data"]
    assert 0 < result.pop("expires_in") <= 3600
    second.pop("expires_in")
    assert result == second
    assert (await client.get(path, headers=admin)).status_code == 405

    async with container() as scope:
        balances = await scope.get(IWalletBalanceService)
        assert await balances.find(customer_id) is None


async def test_deposits_require_shop_access(
    app: FastAPI, client: AsyncClient
) -> None:
    path = "/admin/wallets/1/deposits"
    detail = f"{path}/c119ee11-a4d6-4e31-ad14-877e0ed6c4b0"
    assert (await client.get(detail)).status_code == 401
    assert (await client.post(path, json={"amount": 1})).status_code == 401
    headers = await _headers(app, client, super_admin=False, suffix=2)
    assert (await client.get(detail, headers=headers)).status_code == 403
    forbidden = await client.post(path, headers=headers, json={"amount": 1})
    assert forbidden.status_code == 403


async def test_list_payment_methods(app: FastAPI, client: AsyncClient) -> None:
    admin = await _headers(app, client, super_admin=True, suffix=3)
    customer_id = await _customer(client, admin)
    path = f"/admin/wallets/{customer_id}/deposits/methods"
    assert (await client.get(path, params={"amount": 100})).status_code == 401
    assert (
        await client.get(path, headers=admin, params={"amount": 0})
    ).status_code == 422
    amount = 100_000_000
    gateway = await client.post(
        "/admin/crypto-gateways",
        headers=admin,
        json={
            "kind": "plisio",
            "title": "Top-up Gateway",
            "icon_url": "/media/top-up.png",
            "min_amount": amount,
            "max_amount": amount * 2,
            "is_active": True,
        },
    )
    assert gateway.status_code == 201, gateway.text
    gateway_id = gateway.json()["data"]["id"]
    gateway_path = f"/admin/crypto-gateways/{gateway_id}"
    empty = await client.get(path, headers=admin, params={"amount": amount})
    assert empty.status_code == 200, empty.text
    assert gateway_id not in [
        item["id"] for item in empty.json()["data"]["gateways"]
    ]
    config = await client.put(
        f"{gateway_path}/config",
        headers=admin,
        json={
            "kind": "plisio",
            "api_url": "https://api.plisio.net/api/v1",
            "api_key": "test-deposit-gateway-credential",
            "price_currency": "USD",
        },
    )
    assert config.status_code == 200, config.text
    for value in (amount, amount * 2):
        response = await client.get(
            path, headers=admin, params={"amount": value}
        )
        assert response.status_code == 200, response.text
        data = response.json()["data"]
        assert (data["customer_id"], data["amount"], data["currency"]) == (
            customer_id,
            value,
            "IRR",
        )
        assert "card_to_card" in data
        assert {
            "id": gateway_id,
            "kind": "plisio",
            "title": "Top-up Gateway",
            "icon_url": "/media/top-up.png",
            "min_amount": amount,
            "max_amount": amount * 2,
            "price_currency": "USD",
        } in data["gateways"]
        assert response.json()["meta"]["total_items"] >= 1
        assert "test-deposit-gateway-credential" not in response.text
    for value in (amount - 1, amount * 2 + 1):
        response = await client.get(
            path, headers=admin, params={"amount": value}
        )
        ids = [item["id"] for item in response.json()["data"]["gateways"]]
        assert gateway_id not in ids
    extra_page = await client.get(
        path, headers=admin, params={"amount": amount, "page": INT64_MAX}
    )
    assert extra_page.json()["data"]["gateways"] == []
    assert extra_page.json()["meta"]["total_items"] >= 1
    updated = await client.patch(
        gateway_path, headers=admin, json={"is_active": False}
    )
    assert updated.status_code == 200, updated.text
    disabled = await client.get(path, headers=admin, params={"amount": amount})
    assert gateway_id not in [
        item["id"] for item in disabled.json()["data"]["gateways"]
    ]
    assert (
        await client.delete(gateway_path, headers=admin)
    ).status_code == 200

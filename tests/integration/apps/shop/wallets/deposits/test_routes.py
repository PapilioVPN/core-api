"""Issue and read expiring top-up invoices through the panel."""

from datetime import datetime, timedelta
from json import loads
from os import environ
from typing import cast
from uuid import UUID

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.infra.db.transaction import transaction
from papilio.infra.redis.client import RedisClient, resolve
from papilio.types.constants import INT64_MAX

from src.apps.core.access.roles.app.interfaces.services import IRoleService
from src.apps.core.access.roles.domain.dtos.records import RoleCreate
from src.apps.core.access.users.app.interfaces.commands import (
    IUserCreateCommand,
)
from src.apps.core.access.users.domain.dtos.records import UserCreate
from src.apps.shop.banking.banks.domain.models.records import BankModel
from src.apps.shop.banking.banks.infra.pg.repositories.records import (
    BankRepository,
)
from src.apps.shop.billing.payments.infra.pg.repositories.crud import (
    PaymentRepository,
)
from src.apps.shop.wallets.balance.app.interfaces.services import (
    IWalletBalanceService,
)
from src.apps.shop.wallets.deposits.domain.errors import (
    DepositInvoiceUnavailable,
)
from src.apps.shop.wallets.deposits.domain.models.records import DepositInvoice
from src.apps.shop.wallets.deposits.infra.redis.cache import WalletDepositCache
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


async def _card(
    app: FastAPI, client: AsyncClient, headers: dict[str, str], number: str
) -> int:
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        banks = await scope.get(BankRepository)
        async with transaction():
            bank = await banks.create(
                BankModel(code=number[:6], title="Top-up Test Bank")
            )
        bank_id = bank.id
    prefix = await client.post(
        "/admin/card-prefixes",
        headers=headers,
        json={"bank_id": bank_id, "prefix": number[:6]},
    )
    assert prefix.status_code == 201, prefix.text
    card = await client.post(
        "/admin/payment-cards",
        headers=headers,
        json={
            "card_number": number,
            "holder_name": "Wallet Owner",
            "allow_auto": True,
        },
    )
    assert card.status_code == 201, card.text
    return card.json()["data"]["id"]


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
    settings = "/admin/payment-settings"
    policy = (await client.get(settings, headers=admin)).json()["data"]
    manual = await client.put(
        settings, headers=admin, json={**policy, "auto_confirm": False}
    )
    assert manual.status_code == 200, manual.text
    method = {"method": "card_to_card"}
    assert (
        await client.post(path, headers=admin, json={"amount": 500})
    ).status_code == 422
    unavailable = await client.post(
        path, headers=admin, json={**method, "amount": 500}
    )
    assert unavailable.status_code == 400, unavailable.text
    assert unavailable.json()["error"]["loc"] == ["method"]
    card_number = "9918980000000005"
    card_id = await _card(app, client, admin, card_number)

    for amount in (0, -1, "100", True, INT64_MAX + 1):
        invalid = await client.post(
            path, headers=admin, json={**method, "amount": amount}
        )
        assert invalid.status_code == 422, invalid.text
    missing = await client.post(
        f"/admin/wallets/{INT64_MAX}/deposits",
        headers=admin,
        json={**method, "amount": 1},
    )
    assert missing.status_code == 404, missing.text

    created = await client.post(
        path,
        headers=admin,
        json={**method, "amount": INT64_MAX, "customer_id": other_id},
    )
    assert created.status_code == 201, created.text
    first = created.json()["data"]
    assert first["customer_id"] == customer_id
    assert first["amount"] == INT64_MAX
    assert first["payment"]["final_amount"] == INT64_MAX
    assert first["payment"]["method"] == "card_to_card"
    assert first["payment"]["mode"] == "manual"
    assert first["payment"]["currency"] == "IRR"
    assert first["payment"]["card_number"] == card_number
    assert first["payment"]["holder_name"] == "Wallet Owner"
    assert first["payment"]["bank_title"] == "Top-up Test Bank"
    assert UUID(first["id"]).version == 4
    expires = datetime.fromisoformat(first["expires_at"])
    started = datetime.fromisoformat(first["created_at"])
    assert (expires - started).total_seconds() == 3600
    assert 0 < first.pop("expires_in") <= 3600

    created = await client.post(
        path, headers=admin, json={**method, "amount": 500}
    )
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
    key = f"shop:wallets:deposits:v2:{customer_id}"
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
    assert (
        await client.delete(f"/admin/payment-cards/{card_id}", headers=admin)
    ).status_code == 200
    assert (
        await client.put(settings, headers=admin, json=policy)
    ).status_code == 200


@pytest.mark.skipif(
    not environ.get("PAPILIOVPN_TEST_REDIS_URL"),
    reason="Set PAPILIOVPN_TEST_REDIS_URL to the isolated test Redis",
)
async def test_automatic_invoice_reserves_amount(
    app: FastAPI, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    admin = await _headers(app, client, super_admin=True, suffix=4)
    customer_id = await _customer(client, admin)
    path = f"/admin/wallets/{customer_id}/deposits"
    settings = "/admin/payment-settings"
    policy = (await client.get(settings, headers=admin)).json()["data"]
    auto = await client.put(
        settings,
        headers=admin,
        json={**policy, "auto_confirm": True, "digits": 4},
    )
    assert auto.status_code == 200, auto.text
    number = "9918990000000004"
    card_id = await _card(app, client, admin, number)
    cards = await client.get(
        "/admin/payment-cards",
        headers=admin,
        params={"is_active": True, "allow_auto": True},
    )
    numbers = {row["card_number"] for row in cards.json()["data"]}
    amount = 187_653_115
    body = {"method": "card_to_card", "amount": amount}

    async def fail_save(
        cache: WalletDepositCache, invoice: DepositInvoice
    ) -> DepositInvoice:
        raise DepositInvoiceUnavailable()

    with monkeypatch.context() as cache:
        cache.setattr(WalletDepositCache, "save", fail_save)
        failure = await client.post(path, headers=admin, json=body)
    assert failure.status_code == 503, failure.text
    payments = await client.get(
        "/admin/payments", headers=admin, params={"amount": amount}
    )
    assert payments.json()["data"] == []

    created = await client.post(path, headers=admin, json=body)
    assert created.status_code == 201, created.text
    data = created.json()["data"]
    payment = data["payment"]
    assert data["amount"] == amount
    assert payment["mode"] == "auto"
    assert payment["card_number"] in numbers
    assert payment["final_amount"] != amount
    assert payment["confirmation_code"] == str(payment["final_amount"])[-4:]
    assert "payment_id" not in payment
    payments = await client.get(
        "/admin/payments", headers=admin, params={"amount": amount}
    )
    (reserved,) = payments.json()["data"]
    assert reserved["transfer_amount"] == payment["final_amount"]
    assert reserved["receipt_id"] is None
    assert reserved["status"] == "pending"
    container = cast(AsyncContainer, app.state.dishka_container)
    redis = await container.get(RedisClient)
    raw = await resolve(
        redis.client.hget(
            f"shop:wallets:deposits:v2:{customer_id}", data["id"]
        )
    )
    assert raw is not None
    assert loads(raw)["payment"]["payment_id"] == reserved["id"]
    async with container() as scope:
        balance = await scope.get(IWalletBalanceService)
        assert await balance.find(customer_id) is None
        repo = await scope.get(PaymentRepository)
        async with transaction():
            await repo.remove_by_id(reserved["id"])
    assert (
        await client.delete(f"/admin/payment-cards/{card_id}", headers=admin)
    ).status_code == 200
    assert (
        await client.put(settings, headers=admin, json=policy)
    ).status_code == 200


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

"""Record and review manual card transfers through the customer panel."""

from asyncio import gather
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.infra.db.uow import PGUnitOfWork
from sqlalchemy import insert
from sqlmodel import col

from src.apps.core.auth.domain.enums.permissions import AdminPermission
from src.apps.core.roles.app.interfaces.services import (
    IRoleScopeService,
    IRoleService,
)
from src.apps.core.roles.domain.dtos.role_scopes import RoleScopeCreate
from src.apps.core.scopes.app.interfaces.services import IScopeService
from src.apps.core.scopes.domain.dtos.records import ScopeCreate
from src.apps.shop.banking.banks.infra.pg.tables import BankTable

pytestmark = pytest.mark.integration
URL = "/admin/payments"
CARDS = "/admin/payment-cards"


@pytest.mark.parametrize("admin", [("074", True)], indirect=True)
async def test_manual_payments(
    app: FastAPI, client: AsyncClient, admin: dict[str, str]
) -> None:
    assert (await client.get(URL)).status_code == 401
    customer = await client.post(
        "/admin/customers", headers=admin, json={"name": "Payment Customer"}
    )
    assert customer.status_code == 201
    customer_id = customer.json()["data"]["id"]

    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        uow = await scope.get(PGUnitOfWork)
        async with uow.transaction():
            result = await uow.execute(
                insert(BankTable)
                .values(code="payment-test", title="Test Bank")
                .returning(col(BankTable.id))
            )
            bank_id = result.scalar_one()
    prefix = await client.post(
        "/admin/card-prefixes",
        headers=admin,
        json={"bank_id": bank_id, "prefix": "990074"},
    )
    assert prefix.status_code == 201
    card = await client.post(
        CARDS,
        headers=admin,
        json={"card_number": "9900740000000003", "holder_name": "Test Holder"},
    )
    assert card.status_code == 201, card.text
    card_id = card.json()["data"]["id"]

    data = {
        "customer_id": customer_id,
        "card_id": card_id,
        "amount": 4_000_000_005,
        "reference": "ref-125_3",
        "paid_at": "2026-11-23T12:30:00+03:30",
    }
    for amount in (0, -1, 1.5, 2**63):
        invalid = await client.post(
            URL, headers=admin, json=data | {"amount": amount}
        )
        assert invalid.status_code == 422
    missing = await client.post(
        URL, headers=admin, json=data | {"customer_id": 99999}
    )
    assert missing.status_code == 404
    missing = await client.post(
        URL, headers=admin, json=data | {"card_id": 99999}
    )
    assert missing.status_code == 404
    response = await client.post(URL, headers=admin, json=data)
    assert response.status_code == 201
    pending = response.json()["data"]
    path = f"{URL}/{pending['id']}"
    assert pending["customer_id"] == customer_id
    assert pending["amount"] == data["amount"]
    assert pending["bank_id"] == bank_id
    assert pending["card_last4"] == "0003"
    assert pending["status"] == "pending"
    assert pending["reviewer_id"] is None
    assert pending["reviewed_at"] is None
    assert pending["paid_at"].startswith("2026-11-23T09:00:00")

    reviewed = await client.post(
        URL,
        headers=admin,
        json=data | {"reference": "other-transfer", "paid_at": None},
    )
    other_path = f"{URL}/{reviewed.json()['data']['id']}"
    assert (
        await client.patch(
            other_path, headers=admin, json={"status": "rejected"}
        )
    ).json()["data"]["status"] == "rejected"

    rows = await client.get(
        URL,
        headers=admin,
        params={
            "q": "125_",
            "customer_id": customer_id,
            "card_id": card_id,
            "status": "pending",
            "per_page": 1,
        },
    )
    assert rows.json()["meta"]["total_items"] == 1
    assert rows.json()["data"] == [pending]
    literal = await client.get(URL, headers=admin, params={"q": "%"})
    assert literal.json()["data"] == []
    batch = await client.get(
        f"{URL}/batch",
        headers=admin,
        params={"ids": [pending["id"], pending["id"], 99999]},
    )
    assert batch.json()["data"] == [pending]
    assert (
        await client.patch(path, headers=admin, json={"status": "pending"})
    ).status_code == 422
    assert (
        await client.patch(
            f"{URL}/99999", headers=admin, json={"status": "rejected"}
        )
    ).status_code == 404

    decisions = await gather(
        client.patch(path, headers=admin, json={"status": "confirmed"}),
        client.patch(path, headers=admin, json={"status": "rejected"}),
    )
    assert sorted(response.status_code for response in decisions) == [200, 409]
    saved = next(
        response.json()["data"]
        for response in decisions
        if response.is_success
    )
    assert saved["status"] in ("confirmed", "rejected")
    assert saved["reviewer_id"] > 0
    assert saved["reviewed_at"] is not None
    assert (await client.get(path, headers=admin)).json()["data"] == saved
    assert (
        await client.patch(
            path, headers=admin, json={"status": saved["status"]}
        )
    ).status_code == 409

    assert (
        await client.delete(f"{CARDS}/{card_id}", headers=admin)
    ).status_code == 200
    historical = (await client.get(path, headers=admin)).json()["data"]
    assert historical == saved | {"card_id": None}


@pytest.mark.parametrize("admin", [("075", False)], indirect=True)
async def test_payments_require_operation_grants(
    app: FastAPI, client: AsyncClient, admin: dict[str, str]
) -> None:
    assert (await client.get(URL, headers=admin)).status_code == 403

    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.find_by_key("customer-test-075")
        assert role is not None
        scopes = await scope.get(IScopeService)
        customers = await scopes.find_by_key("customers")
        created = customers is None
        if customers is None:
            customers = await scopes.create(
                ScopeCreate(key="customers", title="Customers")
            )
        grants = await scope.get(IRoleScopeService)
        await grants.create(
            role.id,
            RoleScopeCreate(
                scope_id=customers.id, permissions=AdminPermission.READ
            ),
        )

    assert (await client.get(URL, headers=admin)).status_code == 200
    assert (
        await client.post(
            URL,
            headers=admin,
            json={
                "customer_id": 1,
                "card_id": 1,
                "amount": 1,
                "reference": "receipt",
            },
        )
    ).status_code == 403
    assert (
        await client.patch(
            f"{URL}/1", headers=admin, json={"status": "confirmed"}
        )
    ).status_code == 403

    async with container() as scope:
        grants = await scope.get(IRoleScopeService)
        await grants.remove(role.id, customers.id)
        if created:
            scopes = await scope.get(IScopeService)
            await scopes.remove(customers.id)

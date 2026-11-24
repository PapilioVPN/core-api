"""Register pending payments internally and read them from the panel."""

from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.errors.exceptions import NotFoundException
from pydantic import ValidationError

from src.apps.core.access.auth.domain.enums.permissions import AdminPermission
from src.apps.core.access.roles.app.interfaces.services import (
    IRoleScopeService,
    IRoleService,
)
from src.apps.core.access.roles.domain.dtos.records import RoleCreate
from src.apps.core.access.roles.domain.dtos.role_scopes import RoleScopeCreate
from src.apps.core.access.scopes.app.interfaces.services import IScopeService
from src.apps.core.access.scopes.domain.dtos.records import ScopeCreate
from src.apps.core.access.users.app.interfaces.commands import (
    IUserCreateCommand,
)
from src.apps.core.access.users.domain.dtos.records import UserCreate
from src.apps.shop.billing.payments.app.interfaces.commands import (
    IPaymentCommand,
)
from src.apps.shop.billing.payments.domain.dtos.records import (
    PaymentCreate,
)
from src.apps.shop.billing.payments.domain.enums.records import (
    PaymentSource,
)
from src.apps.shop.customers.profiles.app.interfaces.services import (
    ICustomerService,
)
from src.apps.shop.customers.profiles.domain.dtos.records import ProfileCreate

pytestmark = pytest.mark.integration
URL = "/admin/payments"


async def test_payments(app: FastAPI, client: AsyncClient) -> None:
    assert (await client.get(URL)).status_code == 401

    password = "isolated-billing-operator-password"
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.create(
            RoleCreate(key="billing-tests", title="Billing Operator")
        )
        role_id = role.id
        users = await scope.get(IUserCreateCommand)
        user = await users.create(
            UserCreate(
                first_name="Billing",
                last_name="Operator",
                role_id=role_id,
                mobile="09120000074",
                password=password,
            ),
            super_admin=False,
        )
        mobile = user.mobile
        profiles = await scope.get(ICustomerService)
        customer = await profiles.create(
            ProfileCreate(name="Billing Test Customer")
        )
        customer_id = customer.id
        payments = await scope.get(IPaymentCommand)
        data = {
            "customer_id": customer_id,
            "source": PaymentSource.ORDER_PAYMENT,
            "source_id": 51,
            "amount": 4_000_000_005,
        }
        for amount in (0, -1, 1.5, 2**63):
            with pytest.raises(ValidationError):
                PaymentCreate.model_validate(data | {"amount": amount})
        with pytest.raises(ValidationError):
            PaymentCreate.model_validate(data | {"source": "unknown"})
        with pytest.raises(NotFoundException):
            await payments.create(
                PaymentCreate.model_validate(data | {"customer_id": 99999})
            )

        order = await payments.create(PaymentCreate.model_validate(data))
        topup = await payments.create(
            PaymentCreate.model_validate(
                data | {"source": PaymentSource.WALLET_TOPUP}
            )
        )

    token = await client.post(
        "/admin/auth/tokens",
        json={"mobile": mobile, "password": password},
    )
    assert token.status_code == 200
    headers = {
        "Authorization": f"Bearer {token.json()['data']['access_token']}"
    }
    path = f"{URL}/{order.id}"
    assert (await client.get(path, headers=headers)).status_code == 403
    assert (await client.get(URL, headers=headers)).status_code == 403

    async with container() as scope:
        scopes = await scope.get(IScopeService)
        billing = await scopes.create(
            ScopeCreate(key="billing", title="Billing")
        )
        grants = await scope.get(IRoleScopeService)
        await grants.create(
            role_id,
            RoleScopeCreate(
                scope_id=billing.id, permissions=AdminPermission.READ
            ),
        )

    assert (
        await client.post(URL, headers=headers, json=data)
    ).status_code == 405
    detail = await client.get(path, headers=headers)
    assert detail.status_code == 200
    payment = detail.json()["data"]
    assert payment["amount"] == data["amount"]
    assert payment["customer_id"] == customer_id
    assert payment["source"] == "order_payment"
    assert payment["source_id"] == 51
    assert payment["status"] == "pending"
    assert payment["submitted_at"] is None

    batch = await client.get(
        f"{URL}/batch",
        headers=headers,
        params={"ids": [order.id, order.id, 99999]},
    )
    assert batch.json()["data"] == [payment]
    filtered = await client.get(
        URL,
        headers=headers,
        params={
            "source": "order_payment",
            "source_id": 51,
            "customer_id": customer_id,
            "status": "pending",
        },
    )
    assert filtered.json()["data"] == [payment]
    assert filtered.json()["meta"]["total_items"] == 1
    page = await client.get(
        URL, headers=headers, params={"source_id": 51, "per_page": 1}
    )
    assert page.json()["meta"]["total_items"] == 2
    assert page.json()["data"][0]["id"] == topup.id
    assert (
        await client.get(f"{URL}/99999", headers=headers)
    ).status_code == 404

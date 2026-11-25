"""Exercise crypto invoice issuance and authenticated provider settlement."""

from decimal import Decimal
from hmac import digest
from json import dumps, loads
from secrets import randbelow
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient, MockTransport, ReadTimeout, Request, Response
from papilio.infra.db.transaction import active_transaction
from papilio.infra.db.uow import UnitOfWork
from papilio.infra.http.connection import HTTPConnection

from src.apps.core.access.roles.app.interfaces.services import IRoleService
from src.apps.core.access.roles.domain.dtos.records import RoleCreate
from src.apps.core.access.users.app.interfaces.commands import (
    IUserCreateCommand,
)
from src.apps.core.access.users.domain.dtos.records import UserCreate
from src.apps.shop.crypto.gateways.app.interfaces.services import (
    ICryptoGatewayService,
)
from src.apps.shop.crypto.gateways.domain.dtos.records import GatewayCreate
from src.apps.shop.crypto.payments.config import CryptoPaymentsConfig
from src.settings.config import CoreSettings

pytestmark = pytest.mark.integration


@pytest.fixture
def pg(pg: CoreSettings) -> CoreSettings:
    pg.crypto_payments = CryptoPaymentsConfig.model_validate(
        {
            "nowpayments": {
                "test-merchant": {
                    "api_url": "https://provider.example.test/v1",
                    "callback_base_url": "https://shop.example.test",
                    "api_key": "test-key",
                    "ipn_secret": "test-ipn-secret",
                    "price_decimals": 2,
                }
            }
        }
    )
    return pg


async def test_issue_requires_admin(client: AsyncClient) -> None:
    response = await client.post(
        "/admin/crypto-payments", json={"gateway_id": 1, "amount": 100_000}
    )
    assert response.status_code == 401
    assert (await client.get("/admin/crypto-payments")).status_code == 401


async def test_unknown_hook(client: AsyncClient) -> None:
    response = await client.post("/hooks/crypto-payments/1", json={})
    assert response.status_code == 401


async def test_issue_and_settle(app: FastAPI, client: AsyncClient) -> None:
    endpoint = "/admin/crypto-payments"
    password = "isolated-crypto-operator-password"
    suffix = randbelow(10**7)
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.create(
            RoleCreate(key=f"crypto-{suffix}", title="Crypto Operator")
        )
        users = await scope.get(IUserCreateCommand)
        user = await users.create(
            UserCreate(
                first_name="Crypto",
                last_name="Operator",
                mobile=f"0931{suffix:07d}",
                role_id=role.id,
                password=password,
            ),
            super_admin=True,
        )
        gateways = await scope.get(ICryptoGatewayService)
        gateway = await gateways.create(
            GatewayCreate(
                key="test-merchant",
                title="Test merchant",
                kind="nowpayments",
                price_currency="EUR",
                pay_currency="TRX",
                rial_rate=Decimal("600000"),
                is_active=True,
            )
        )
    login = await client.post(
        "/admin/auth/tokens",
        json={"mobile": user.mobile, "password": password},
    )
    assert login.is_success, login.text
    headers = {
        "Authorization": f"Bearer {login.json()['data']['access_token']}"
    }

    hook = f"/hooks/crypto-payments/{gateway.id}"
    invoice_id = "6700"
    provider_id = "12345"
    invoice_url = f"https://checkout.example.test/invoice/{invoice_id}"
    status = {
        "invoice_id": invoice_id,
        "payment_id": provider_id,
        "payment_status": "finished",
        "price_amount": "9.17",
        "price_currency": "eur",
        "pay_amount": "30.1",
        "pay_currency": "trx",
        "actually_paid": "25.5",
    }
    issued_count = 0
    checks = 0
    deny_issue = False

    def provider(request: Request) -> Response:
        nonlocal checks, issued_count
        assert request.headers["x-api-key"] == "test-key"
        assert str(request.url.host) == "provider.example.test"
        assert active_transaction() is None
        unit = UnitOfWork.current()
        assert unit is not None and not unit.session.in_transaction()
        if request.method == "POST":
            assert request.url.path == "/v1/invoice"
            issued_count += 1
            data = loads(request.content)
            assert (
                data["ipn_callback_url"] == f"https://shop.example.test{hook}"
            )
            assert data["price_amount"] == "9.17"
            assert data["price_currency"] == "eur"
            assert data["pay_currency"] == "trx"
            if deny_issue:
                raise ReadTimeout(
                    "uncertain invoice creation", request=request
                )
            status["order_id"] = data["order_id"]
            response = Response(
                200,
                json={
                    **data,
                    "id": int(invoice_id),
                    "invoice_url": invoice_url,
                },
            )
        else:
            assert request.url.path == f"/v1/payment/{provider_id}"
            checks += 1
            response = Response(200, json=status)
        return response

    ipn = {
        "payment_id": int(provider_id),
        "invoice_id": int(invoice_id),
        "payment_status": "finished",
        "fee": {"withdrawalFee": 0.001, "currency": "trx"},
    }
    signed = dumps(ipn, sort_keys=True, separators=(",", ":")).encode()
    signature = digest(b"test-ipn-secret", signed, "sha512").hex()
    callback_headers = {"x-nowpayments-sig": signature}
    connection = await container.get(HTTPConnection)
    original = connection.client

    async with AsyncClient(transport=MockTransport(provider)) as upstream:
        connection.client = upstream
        try:
            payload = {"gateway_id": gateway.id, "amount": 5_500_000}
            response = await client.post(
                endpoint, headers=headers, json=payload
            )
            assert response.status_code == 201, response.text
            payment = response.json()["data"]
            assert payment["status"] == "pending"
            assert payment["price_amount"] == "9.17"
            assert payment["invoice_url"] == invoice_url
            detail = f"{endpoint}/{payment['id']}"

            invalid = await client.post(
                hook, headers=callback_headers, json={**ipn, "invoice_id": 8}
            )
            assert invalid.status_code == 401
            assert checks == 0
            status["price_currency"] = "usd"
            mismatch = await client.post(
                hook, headers=callback_headers, json=ipn
            )
            assert mismatch.status_code == 409, mismatch.text
            found = await client.get(detail, headers=headers)
            assert found.json()["data"]["status"] == "pending"

            status["price_currency"] = "eur"
            partial = await client.post(
                hook, headers=callback_headers, json=ipn
            )
            assert partial.status_code == 204, partial.text
            found = (await client.get(detail, headers=headers)).json()["data"]
            assert found["status"] == "partial"
            assert found["confirmed_at"] is None
            assert found["provider_payment_id"] is None

            # The callback's status is advisory; the authenticated read wins.
            status["actually_paid"] = "30.1"
            settled = await client.post(
                hook, headers=callback_headers, json=ipn
            )
            assert settled.status_code == 204, settled.text
            confirmed = (await client.get(detail, headers=headers)).json()[
                "data"
            ]
            assert confirmed["status"] == "confirmed"
            assert confirmed["provider_payment_id"] == provider_id
            assert confirmed["confirmed_at"] is not None

            checked_before = checks
            again = await client.post(hook, headers=callback_headers, json=ipn)
            assert again.status_code == 204
            assert checks == checked_before
            assert (await client.get(detail, headers=headers)).json()[
                "data"
            ] == confirmed

            deny_issue = True
            response = await client.post(
                endpoint, headers=headers, json=payload
            )
            assert response.status_code == 502, response.text
            attempt = response.json()["data"]["id"]
            saved = await client.get(f"{endpoint}/{attempt}", headers=headers)
            assert saved.json()["data"]["invoice_id"] is None
            assert saved.json()["data"]["status"] == "pending"
            assert issued_count == 2

            params = {"gateway_id": gateway.id, "amount": payload["amount"]}
            page = await client.get(
                endpoint, headers=headers, params={**params, "per_page": 1}
            )
            assert page.status_code == 200, page.text
            assert [row["id"] for row in page.json()["data"]] == [attempt]
            assert page.json()["meta"]["total_items"] == 2

            missing = await client.get(
                endpoint,
                headers=headers,
                params={**params, "has_invoice": False, "status": "pending"},
            )
            assert [row["id"] for row in missing.json()["data"]] == [attempt]

            completed = await client.get(
                endpoint,
                headers=headers,
                params={
                    **params,
                    "invoice_id": invoice_id,
                    "provider_payment_id": provider_id,
                    "status": "confirmed",
                    "created_since": confirmed["created_at"],
                    "created_until": saved.json()["data"]["created_at"],
                },
            )
            assert completed.json()["data"] == [confirmed]
            assert checks == checked_before

            invalid_range = await client.get(
                endpoint,
                headers=headers,
                params={
                    "created_since": confirmed["created_at"],
                    "created_until": confirmed["created_at"],
                },
            )
            assert invalid_range.status_code == 400
            assert (
                invalid_range.json()["error"]["message_code"]
                == "invalid_payment_range"
            )

            empty = await client.get(
                endpoint,
                headers=headers,
                params={**params, "status": "partial"},
            )
            assert empty.json()["data"] == []
            assert empty.json()["meta"]["total_items"] == 0
        finally:
            connection.client = original

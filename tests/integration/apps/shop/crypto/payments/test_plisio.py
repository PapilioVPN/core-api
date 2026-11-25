"""Verify the Plisio protocol and the shared payment state on PostgreSQL."""

from decimal import Decimal
from hmac import digest
from json import dumps
from logging import INFO
from secrets import randbelow
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient, MockTransport, Request, Response
from papilio.infra.db.transaction import active_transaction
from papilio.infra.http.connection import HTTPConnection
from pydantic import JsonValue

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

pytestmark = pytest.mark.integration


async def test_plisio_payment(
    app: FastAPI, client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    endpoint = "/admin/crypto-payments"
    password = "isolated-plisio-operator-password"
    suffix = randbelow(10**7)
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.create(
            RoleCreate(key=f"plisio-{suffix}", title="Plisio Operator")
        )
        users = await scope.get(IUserCreateCommand)
        user = await users.create(
            UserCreate(
                first_name="Plisio",
                last_name="Operator",
                mobile=f"0919{suffix:07d}",
                role_id=role.id,
                password=password,
            ),
            super_admin=True,
        )
        gateways = await scope.get(ICryptoGatewayService)
        gateway = await gateways.create(
            GatewayCreate(
                key="test-plisio",
                title="Plisio Test",
                kind="plisio",
                price_currency="EUR",
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

    config_path = f"/admin/crypto-gateways/{gateway.id}/config"
    config = {
        "kind": "plisio",
        "api_url": "https://api.plisio.net/api/v1",
        "callback_base_url": "https://shop.example.test",
        "api_key": "test-plisio-secret",
        "price_decimals": 3,
    }
    configured = await client.put(config_path, headers=headers, json=config)
    assert configured.is_success, configured.text
    assert configured.json()["data"]["has_api_key"] is True
    assert config["api_key"] not in configured.text

    hook = f"/hooks/crypto-payments/plisio/{gateway.id}"
    parent = "5ee0e502283675293c450d0e"
    child = "5ee210133f5a5e30771f0283"
    operation: dict[str, JsonValue] = {
        "id": child,
        "parent_id": parent,
        "type": "invoice",
        "status": "completed",
        "psys_cid": "USDT_TRX",
        "sum": "22.10",
        "actual_sum": "22.09",
    }
    checks = 0

    def provider(request: Request) -> Response:
        nonlocal checks
        data: dict[str, JsonValue]
        assert active_transaction() is None
        assert request.method == "GET"
        assert request.url.host == "api.plisio.net"
        assert request.url.params["api_key"] == "test-plisio-secret"
        if request.url.path == "/api/v1/invoices/new":
            args = request.url.params
            assert args["source_amount"] == "9.167"
            assert args["source_currency"] == "EUR"
            assert (
                args["callback_url"]
                == f"https://shop.example.test{hook}?json=true"
            )
            assert "currency" not in args
            operation["params"] = {
                "order_number": args["order_number"],
                "source_amount": args["source_amount"],
                "source_currency": args["source_currency"],
            }
            data = {
                "txn_id": parent,
                "invoice_url": "https://checkout.example.test/plisio",
            }
        else:
            assert request.url.path == f"/api/v1/operations/{child}"
            checks += 1
            data = operation
        return Response(200, json={"status": "success", "data": data})

    notice = {"txn_id": child, "status": "completed", "switch_id": parent}
    value = dumps(notice, separators=(",", ":")).encode()
    signature = digest(b"test-plisio-secret", value, "sha1").hex()
    signed = {**notice, "verify_hash": signature}

    connection = await container.get(HTTPConnection)
    original = connection.client
    async with AsyncClient(transport=MockTransport(provider)) as upstream:
        connection.client = upstream
        try:
            with caplog.at_level(INFO, logger="httpx"):
                response = await client.post(
                    endpoint,
                    headers=headers,
                    json={"gateway_id": gateway.id, "amount": 5_500_000},
                )
                assert response.status_code == 201, response.text
                payment = response.json()["data"]
                assert payment["invoice_id"] == parent
                detail = f"{endpoint}/{payment['id']}"
                rejected = await client.post(
                    hook, json={**signed, "status": "underpaid"}
                )
                assert rejected.status_code == 401
                wrong_path = await client.post(
                    f"/hooks/crypto-payments/{gateway.id}",
                    headers={"x-nowpayments-sig": signature},
                    json=signed,
                )
                assert wrong_path.status_code == 401
                assert checks == 0

                operation["actual_sum"] = None
                missing = await client.post(hook, json=signed)
                assert missing.status_code == 502, missing.text
                saved = (await client.get(detail, headers=headers)).json()[
                    "data"
                ]
                assert saved["status"] == "pending"

                operation["actual_sum"] = "22.09"
                partial = await client.post(hook, json=signed)
                assert partial.status_code == 200, partial.text
                saved = (await client.get(detail, headers=headers)).json()[
                    "data"
                ]
                assert saved["status"] == "partial"
                assert saved["confirmed_at"] is None

                operation["actual_sum"] = "22.10"
                settled = await client.post(hook, json=signed)
                assert settled.status_code == 200, settled.text
                saved = (await client.get(detail, headers=headers)).json()[
                    "data"
                ]
                assert saved["status"] == "confirmed"
                assert saved["provider_payment_id"] == child
                assert saved["confirmed_at"] is not None
                assert (
                    await client.post(hook, json=signed)
                ).status_code == 200
                assert checks == 3
        finally:
            connection.client = original

    assert any(
        record.name == "httpx" and "/invoices/new?" in record.getMessage()
        for record in caplog.records
    )
    assert "test-plisio-secret" not in caplog.text

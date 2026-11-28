"""Exercise IPG link creation with real persistence and controlled HTTP."""

from json import loads
from typing import cast
from uuid import uuid4

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient, MockTransport, ReadTimeout, Request, Response
from papilio.infra.http.connection import HTTPConnection

from src.apps.core.access.auth.domain.enums.permissions import AdminPermission
from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.auth.routers.dependencies.identity import (
    current_admin,
)
from src.apps.finance.ipg.gateways.domain.enums.records import GatewayKind
from src.apps.finance.ipg.payments.app.interfaces.create import (
    ICreatePaymentCommand,
)
from src.apps.finance.ipg.payments.domain.dtos.records import PaymentCreate
from src.apps.finance.ipg.payments.domain.enums.records import LinkStatus
from src.apps.finance.ipg.payments.infra.pg.repositories.crud import (
    PaymentRepository,
)

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    ("kind", "endpoint", "response", "ref", "url"),
    [
        (
            GatewayKind.ZARINPAL,
            "https://payment.zarinpal.com/pg/v4/payment/request.json",
            {
                "data": {
                    "code": 100,
                    "authority": "A00000000000000000000000000012345678",
                }
            },
            "A00000000000000000000000000012345678",
            "https://payment.zarinpal.com/pg/StartPay/A00000000000000000000000000012345678",
        ),
        (
            GatewayKind.ZIBAL,
            "https://gateway.zibal.ir/v1/request",
            {"result": 100, "trackId": 12345678},
            "12345678",
            "https://gateway.zibal.ir/start/12345678",
        ),
    ],
)
async def test_create_ipg_payment(
    app: FastAPI,
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    kind: GatewayKind,
    endpoint: str,
    response: dict[str, object],
    ref: str,
    url: str,
) -> None:
    async def admin() -> AdminIdentity:
        return AdminIdentity(
            1, 1, {"finance": AdminPermission.CREATE}, uuid4(), False
        )

    app.dependency_overrides[current_admin] = admin
    merchant = "fcd1226a-fd39-45dc-b547-cb7a485f8504"
    created = await client.post(
        "/admin/ipg/gateways",
        json={
            "kind": kind,
            "title": "Fixture active gateway",
            "is_active": True,
            "config": {"merchant_id": merchant},
        },
    )
    assert created.status_code == 201, created.text

    data = PaymentCreate.model_validate(
        {
            "kind": kind,
            "amount": 123_456,
            "description": "Fixture purchase",
            "callback_url": "https://merchant.example/callback",
        }
    )
    calls = 0

    def provider(request: Request) -> Response:
        nonlocal calls
        calls += 1
        assert request.method == "POST"
        assert str(request.url) == endpoint
        payload = loads(request.content)
        assert payload["amount"] == data.amount
        assert payload["description"] == data.description
        if kind is GatewayKind.ZARINPAL:
            assert payload["merchant_id"] == merchant
            assert payload["callback_url"] == str(data.callback_url)
            assert payload["currency"] == "IRR"
        else:
            assert payload["merchant"] == merchant
            assert payload["callbackUrl"] == str(data.callback_url)
        if calls == 2:
            raise ReadTimeout("Fixture lost response", request=request)
        return Response(200, json=response)

    container = cast(AsyncContainer, app.state.dishka_container)
    command = await container.get(ICreatePaymentCommand)
    connection = await container.get(HTTPConnection)
    async with AsyncClient(transport=MockTransport(provider)) as upstream:
        with monkeypatch.context() as patch:
            patch.setattr(connection, "client", upstream)
            issued = await command.create(data)
            unknown = await command.create(data)

    assert calls == 2
    assert (issued.status, issued.url) == (LinkStatus.READY, url)
    assert unknown.status is LinkStatus.UNKNOWN and unknown.url is None
    async with container() as scope:
        payments = await scope.get(PaymentRepository)
        stored = await payments.get_by_id(issued.id)
        unresolved = await payments.get_by_id(unknown.id)
    assert stored is not None and stored.reference == ref
    assert stored.amount == data.amount and stored.pay_url == url
    assert stored.gateway_id == created.json()["data"]["id"]
    assert unresolved is not None and unresolved.status is LinkStatus.UNKNOWN

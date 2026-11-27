"""Exercise hosted NOWPayments issuance and signed confirmation."""

from datetime import timedelta
from decimal import Decimal
from hmac import digest
from json import dumps, loads
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient, MockTransport, Request, Response
from papilio.infra.db.uow import PGUnitOfWork, UnitOfWork
from papilio.infra.http.connection import HTTPConnection
from papilio.infra.redis.client import RedisClient
from papilio.utils.dates import utc_now
from sqlalchemy import select

from src.apps.shop.crypto.gateways.app.commands.configs import (
    GatewayConfigCommand,
)
from src.apps.shop.crypto.gateways.app.interfaces.services import (
    ICryptoGatewayService,
)
from src.apps.shop.crypto.gateways.domain.dtos.configs import NowPaymentsConfig
from src.apps.shop.crypto.gateways.domain.dtos.records import GatewayCreate
from src.apps.shop.crypto.payments.app.interfaces.commands import (
    IPaymentCreateCommand,
    IPaymentQuoteCommand,
)
from src.apps.shop.crypto.payments.app.interfaces.issue import (
    IPaymentIssuePipeline,
)
from src.apps.shop.crypto.payments.app.interfaces.services import (
    ICryptoPaymentService,
)
from src.apps.shop.crypto.payments.domain.dtos.records import PaymentCreate
from src.apps.shop.crypto.payments.domain.models.records import (
    CryptoPaymentModel,
)
from src.apps.shop.crypto.payments.domain.results.invoice import Invoice
from src.apps.shop.crypto.payments.infra.broker.config import BrokerConfig
from src.apps.shop.crypto.rates.app.interfaces.cache import IRateCache
from src.apps.shop.crypto.rates.domain.models.records import Rate
from src.bootstrap.outbox import pending

pytestmark = pytest.mark.integration
_SECRET = "test-notification-signing-key"
_CALLBACK = "https://example.test/hooks/crypto"
_HOSTED = "https://nowpayments.io/payment/test"


async def test_confirm_signed_hosted_invoice(
    app: FastAPI, client: AsyncClient
) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    if await container.get(RedisClient | None) is None:
        pytest.skip("Set PAPILIOVPN_TEST_REDIS_URL to the isolated test Redis")
    rates = await container.get(IRateCache)
    await rates.save(
        Rate(
            currency="USD",
            rial_rate=Decimal("600000"),
            source="wallex_usdt",
            fetched_at=utc_now(),
        )
    )
    async with container() as scope:
        gateways = await scope.get(ICryptoGatewayService)
        configs = await scope.get(GatewayConfigCommand)
        create = await scope.get(IPaymentCreateCommand)
        quote = await scope.get(IPaymentQuoteCommand)
        gateway = await gateways.create(
            GatewayCreate(kind="nowpayments", title="Hosted", is_active=True)
        )
        await configs.save(
            gateway.id,
            NowPaymentsConfig.model_validate(
                {
                    "kind": "nowpayments",
                    "api_url": "https://api-sandbox.nowpayments.io/v1",
                    "api_key": "test-api-key",
                    "ipn_secret": _SECRET,
                    "callback_url": _CALLBACK,
                }
            ),
        )
        payment = await create.create(
            PaymentCreate(gateway_id=gateway.id, amount=1_200_000)
        )
        id = payment.id
        frozen = await quote.quote(id, max_age=timedelta(minutes=1))
        assert isinstance(frozen, CryptoPaymentModel)
        assert frozen.quote_amount == Decimal("2")

    def issue(req: Request) -> Response:
        assert UnitOfWork.current() is None
        assert req.url.path == "/v1/invoice"
        assert loads(req.content) == {
            "order_id": str(id),
            "price_amount": 2,
            "price_currency": "usd",
            "ipn_callback_url": _CALLBACK,
        }
        return Response(200, json={"id": 730, "invoice_url": _HOSTED})

    pipeline = await container.get(IPaymentIssuePipeline)
    connection = await container.get(HTTPConnection)
    original = connection.client
    async with AsyncClient(transport=MockTransport(issue)) as provider:
        connection.client = provider
        try:
            invoice = await pipeline.issue(id)
            assert isinstance(invoice, Invoice)
        finally:
            connection.client = original
    assert invoice.id == "730"
    assert invoice.url == _HOSTED

    body = {
        "order_id": str(id),
        "invoice_id": 730,
        "payment_id": 818,
        "price_amount": 2,
        "price_currency": "usd",
        "payment_status": "finished",
        "pay_amount": 0.05,
        "actually_paid": 0.05,
    }
    path = f"/hooks/crypto/nowpayments/{gateway.id}"

    async def notify(data: dict[str, str | int | float]) -> Response:
        encoded = dumps(data, sort_keys=True, separators=(",", ":")).encode()
        signature = digest(_SECRET.encode(), encoded, "sha512").hex()
        return await client.post(
            path, json=data, headers={"x-nowpayments-sig": signature}
        )

    missing = await client.post(
        "/hooks/crypto/nowpayments/9223372036854775807",
        json=body,
        headers={"x-nowpayments-sig": "invalid"},
    )
    assert missing.status_code == 401

    denied = await client.post(
        path, json=body, headers={"x-nowpayments-sig": "invalid"}
    )
    assert denied.status_code == 401
    assert (
        await notify({**body, "payment_status": "confirming"})
    ).status_code == 204
    assert (await notify({**body, "actually_paid": 0.04})).status_code == 409
    assert (await notify({**body, "price_amount": 3})).status_code == 409

    async with container() as scope:
        payments = await scope.get(ICryptoPaymentService)
        before = await payments.get_by_id(id)
        assert before.confirmed_at is None

    for _ in range(2):
        assert (await notify(body)).status_code == 204

    async with container() as scope:
        payments = await scope.get(ICryptoPaymentService)
        saved = await payments.get_by_id(id)
        assert saved.confirmed_at is not None
        assert saved.settlement_id == "818"
        unit = await scope.get(PGUnitOfWork)
        result = await unit.execute(
            select(pending.c.payload).where(
                pending.c.queue == BrokerConfig.confirmed
            )
        )
        assert (
            sum(
                loads(value)["event"] == {"payment_id": id}
                for value in result.scalars()
            )
            == 1
        )

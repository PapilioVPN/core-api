"""Exercise hosted Plisio issuance through the native container."""

from datetime import timedelta
from decimal import Decimal
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient, MockTransport, Request, Response
from papilio.errors.exceptions import ConflictException
from papilio.infra.db.transaction import transaction
from papilio.infra.db.uow import UnitOfWork
from papilio.infra.http.connection import HTTPConnection
from papilio.infra.redis.client import RedisClient
from papilio.utils.dates import utc_now

from src.apps.shop.crypto.gateways.app.commands.configs import (
    GatewayConfigCommand,
)
from src.apps.shop.crypto.gateways.app.interfaces.services import (
    ICryptoGatewayService,
)
from src.apps.shop.crypto.gateways.domain.dtos.configs import (
    PlisioConfig,
    PriceCurrency,
)
from src.apps.shop.crypto.gateways.domain.dtos.records import GatewayCreate
from src.apps.shop.crypto.payments.app.commands.create import (
    PaymentCreateCommand,
)
from src.apps.shop.crypto.payments.app.commands.quote import (
    PaymentQuoteCommand,
)
from src.apps.shop.crypto.payments.app.interfaces.services import (
    ICryptoPaymentService,
)
from src.apps.shop.crypto.payments.app.pipelines.issue import (
    PaymentIssuePipeline,
)
from src.apps.shop.crypto.payments.domain.dtos.records import PaymentCreate
from src.apps.shop.crypto.payments.domain.models.records import (
    CryptoPaymentModel,
)
from src.apps.shop.crypto.payments.domain.results.invoice import Invoice
from src.apps.shop.crypto.payments.domain.results.records import PaymentFailure
from src.apps.shop.crypto.rates.app.interfaces.cache import IRateCache
from src.apps.shop.crypto.rates.domain.models.records import Rate

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    ("currency", "expected"), [("IRR", "1220000"), ("USD", "2.04")]
)
async def test_issue_plisio_invoice(
    app: FastAPI,
    client: AsyncClient,
    caplog: pytest.LogCaptureFixture,
    currency: PriceCurrency,
    expected: str,
) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    if currency == "USD":
        redis = await container.get(RedisClient | None)
        if redis is None:
            pytest.skip(
                "Set PAPILIOVPN_TEST_REDIS_URL to the isolated test Redis"
            )
        rates = await container.get(IRateCache)
        await rates.save(
            Rate(
                currency="USD",
                rial_rate=Decimal("600000"),
                source="wallex_usdt",
                fetched_at=utc_now(),
            )
        )
    secret = "test-hosted-invoice-secret"
    config = PlisioConfig.model_validate(
        {
            "kind": "plisio",
            "api_url": "https://api.plisio.net/api/v1",
            "api_key": secret,
            "price_currency": currency,
        }
    )
    async with container() as scope:
        gateways = await scope.get(ICryptoGatewayService)
        configs = await scope.get(GatewayConfigCommand)
        create = await scope.get(PaymentCreateCommand)
        gateway = await gateways.create(
            GatewayCreate(
                kind="plisio", title="Hosted invoice", is_active=True
            )
        )
        await configs.save(gateway.id, config)
        payment = await create.create(
            PaymentCreate(gateway_id=gateway.id, amount=1_220_000)
        )
        id = payment.id

    pipeline = await container.get(PaymentIssuePipeline)
    with pytest.raises(ConflictException) as exc:
        await pipeline.issue(id)
    assert exc.value.message_code == "crypto_payment_unquoted"

    async with container() as scope:
        configs = await scope.get(GatewayConfigCommand)
        quote = await scope.get(PaymentQuoteCommand)
        frozen = await quote.quote(id, max_age=timedelta(minutes=2))
        assert isinstance(frozen, CryptoPaymentModel)
        assert frozen.quote_currency == currency
        await configs.save(
            gateway.id,
            config.model_copy(
                update={
                    "price_currency": "USD" if currency == "IRR" else "IRR"
                }
            ),
        )

    connection = await container.get(HTTPConnection)
    original = connection.client
    calls = 0
    url = "https://plisio.net/invoice/invoice-123"
    caplog.set_level("INFO", logger="httpx")

    def plisio(request: Request) -> Response:
        nonlocal calls
        calls += 1
        assert UnitOfWork.current() is None
        assert request.method == "GET"
        assert str(request.url.copy_with(query=None)) == (
            "https://api.plisio.net/api/v1/invoices/new"
        )
        assert dict(request.url.params) == {
            "api_key": secret,
            "order_number": str(id),
            "order_name": str(id),
            "source_amount": expected,
            "source_currency": currency,
            "return_existing": "true",
        }
        return (
            Response(503)
            if calls == 1
            else Response(
                200,
                json={
                    "status": "success",
                    "data": {"txn_id": "invoice-123", "invoice_url": url},
                },
            )
        )

    async with AsyncClient(transport=MockTransport(plisio)) as upstream:
        connection.client = upstream
        try:
            assert (
                await pipeline.issue(id) is PaymentFailure.INVOICE_UNAVAILABLE
            )
            invoice = await pipeline.issue(id)
            assert isinstance(invoice, Invoice)
            assert invoice.id == "invoice-123"
            assert invoice.url == url
            assert await pipeline.issue(id) == invoice
            assert calls == 2
        finally:
            connection.client = original
    assert any(
        record.name == "httpx" and "invoices/new" in record.getMessage()
        for record in caplog.records
    )
    assert secret not in caplog.text
    async with container() as scope:
        payments = await scope.get(ICryptoPaymentService)
        async with transaction():
            saved = await payments.get_by_id(id)
            assert saved.invoice_id == invoice.id
            assert saved.invoice_url == invoice.url
            assert saved.quote_currency == currency

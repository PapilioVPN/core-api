"""Verify exact pricing and the frozen quote on a stored payment."""

from datetime import timedelta
from decimal import Decimal
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.infra.db.transaction import transaction
from papilio.infra.redis.client import RedisClient, resolve
from papilio.utils.dates import utc_now

from src.apps.shop.crypto.gateways.app.interfaces.services import (
    ICryptoGatewayService,
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
from src.apps.shop.crypto.payments.domain.dtos.records import PaymentCreate
from src.apps.shop.crypto.payments.domain.models.quote import Quote
from src.apps.shop.crypto.payments.domain.models.records import (
    CryptoPaymentModel,
)
from src.apps.shop.crypto.rates.app.interfaces.cache import IRateCache
from src.apps.shop.crypto.rates.domain.models.records import Rate
from src.apps.shop.crypto.rates.domain.results.records import RateFailure

pytestmark = pytest.mark.integration


async def test_quote_payment(app: FastAPI, client: AsyncClient) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    redis = await container.get(RedisClient | None)
    if redis is None:
        pytest.skip("Set PAPILIOVPN_TEST_REDIS_URL to the isolated test Redis")
    await resolve(redis.client.hdel("shop:crypto:rates", "USD"))
    rates = await container.get(IRateCache)
    max_age = timedelta(minutes=2)
    original = 1_220_000

    async with container() as scope:
        gateways = await scope.get(ICryptoGatewayService)
        create = await scope.get(PaymentCreateCommand)
        plisio = await gateways.create(
            GatewayCreate(kind="plisio", title="Quote IRR", is_active=True)
        )
        nowpayments = await gateways.create(
            GatewayCreate(
                kind="nowpayments", title="Quote USD", is_active=True
            )
        )
        rial = await create.create(
            PaymentCreate(gateway_id=plisio.id, amount=original)
        )
        dollar = await create.create(
            PaymentCreate(gateway_id=nowpayments.id, amount=original)
        )
        rial_id, dollar_id = rial.id, dollar.id

    async with container() as scope:
        command = await scope.get(PaymentQuoteCommand)
        rial = await command.quote(rial_id, max_age=max_age)
        assert isinstance(rial, CryptoPaymentModel)
        assert rial.quote_currency == "IRR"
        assert rial.quote_amount == Decimal(original)
        assert rial.quote_rate is None
        assert (
            await command.quote(dollar_id, max_age=max_age)
        ) is RateFailure.MISSING_RATE
        await rates.save(
            Rate(
                currency="USD",
                rial_rate=Decimal("600000"),
                source="wallex_usdt",
                fetched_at=utc_now() - 2 * max_age,
            )
        )
        assert (
            await command.quote(dollar_id, max_age=max_age)
        ) is RateFailure.STALE_RATE

    async with container() as scope:
        command = await scope.get(PaymentQuoteCommand)
        payments = await scope.get(ICryptoPaymentService)
        async with transaction():
            unpriced = await payments.get_by_id(dollar_id)
            assert unpriced.quote_amount is None
        await rates.save(
            Rate(
                currency="USD",
                rial_rate=Decimal("600000"),
                source="wallex_usdt",
                fetched_at=utc_now(),
            )
        )
        dollar = await command.quote(dollar_id, max_age=max_age)
        assert isinstance(dollar, CryptoPaymentModel)
        assert dollar.amount == original
        assert dollar.quote_currency == "USD"
        assert dollar.quote_amount == Decimal("2.04")
        assert dollar.quote_rate == Decimal("600000")
        await rates.save(
            Rate(
                currency="USD",
                rial_rate=Decimal("900000"),
                source="wallex_usdt",
                fetched_at=utc_now() - 2 * max_age,
            )
        )

    async with container() as scope:
        command = await scope.get(PaymentQuoteCommand)
        replay = await command.quote(dollar_id, max_age=max_age)
        assert isinstance(replay, CryptoPaymentModel)
        assert replay.quote_amount == Decimal("2.04")
        assert replay.quote_rate == Decimal("600000")

        payments = await scope.get(ICryptoPaymentService)
        async with transaction():
            overwritten = await payments.set_quote(
                dollar_id, Quote(amount=Decimal("1.36"), currency="USD")
            )
        assert overwritten is None

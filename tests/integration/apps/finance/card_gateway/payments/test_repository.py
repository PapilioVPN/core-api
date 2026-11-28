"""Exercise hosted card payment persistence through real PostgreSQL."""

from datetime import timedelta
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.infra.db.transaction import transaction
from papilio.utils.dates import utc_now
from sqlalchemy.exc import IntegrityError

from src.apps.finance.card_gateway.gateways.domain.enums.records import (
    GatewayKind,
)
from src.apps.finance.card_gateway.gateways.domain.models.records import (
    GatewayModel,
)
from src.apps.finance.card_gateway.gateways.infra.pg.repositories.crud import (
    GatewayRepository,
)
from src.apps.finance.card_gateway.payments.domain.models.records import (
    PaymentModel,
)
from src.apps.finance.card_gateway.payments.infra.pg.repositories.crud import (
    PaymentRepository,
)

pytestmark = pytest.mark.integration


async def test_link_is_recorded_once_per_payment(
    app: FastAPI, client: AsyncClient
) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    amount = 3_000_000_010
    slug = "fixture-link"
    pay_url = "https://example.invalid/pay/fixture-link"
    expires_at = utc_now() + timedelta(minutes=30)

    async with container() as scope:
        gateways = await scope.get(GatewayRepository)
        payments = await scope.get(PaymentRepository)
        async with transaction():
            first = await gateways.create(
                GatewayModel(
                    title="Primary link fixture",
                    kind=GatewayKind.VARIZA,
                )
            )
            payment = await payments.create(
                PaymentModel(gateway_id=first.id, amount=amount)
            )
            duplicate = await payments.create(
                PaymentModel(gateway_id=first.id, amount=20_000)
            )
        first_id = first.id
        payment_id, duplicate_id = payment.id, duplicate.id
        assert payment.amount == amount
        assert (payment.slug, payment.pay_url, payment.expires_at) == (
            None,
            None,
            None,
        )
        assert await payments.find_by_slug(first_id, slug) is None

        async with transaction():
            linked = await payments.save_link(
                payment_id, slug=slug, pay_url=pay_url, expires_at=expires_at
            )
            assert linked is not None
            assert (linked.id, linked.amount, linked.gateway_id) == (
                payment_id,
                amount,
                first_id,
            )
            assert (linked.slug, linked.pay_url, linked.expires_at) == (
                slug,
                pay_url,
                expires_at,
            )
            assert (
                await payments.save_link(
                    payment_id,
                    slug="replacement-link",
                    pay_url="https://example.invalid/pay/replacement-link",
                    expires_at=None,
                )
                is None
            )
            assert await payments.find_by_slug(first_id + 1, slug) is None

        with pytest.raises(IntegrityError):
            async with transaction():
                await payments.save_link(
                    duplicate_id,
                    slug=slug,
                    pay_url=pay_url,
                    expires_at=expires_at,
                )

    async with container() as scope:
        payments = await scope.get(PaymentRepository)
        stored = await payments.find_by_slug(first_id, slug)
        unlinked = await payments.get_by_id(duplicate_id)
        assert stored is not None and stored.id == payment_id
        assert (stored.pay_url, stored.expires_at) == (pay_url, expires_at)
        assert unlinked is not None and unlinked.slug is None

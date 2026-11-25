"""Verify crypto payment records against PostgreSQL and native discovery."""

from decimal import Decimal
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from papilio.errors.exceptions import ConflictException
from papilio.infra.db.transaction import transaction
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from src.apps.shop.crypto.gateways.app.interfaces.services import (
    ICryptoGatewayService,
)
from src.apps.shop.crypto.gateways.domain.dtos.records import (
    GatewayCreate,
    GatewayUpdate,
)
from src.apps.shop.crypto.payments.domain.dtos.records import (
    CryptoPaymentCreate,
)
from src.apps.shop.crypto.payments.domain.enums.records import (
    CryptoPaymentStatus,
)
from src.apps.shop.crypto.payments.domain.models.records import (
    CryptoPaymentModel,
)
from src.apps.shop.crypto.payments.infra.pg.repositories.crud import (
    CryptoPaymentRepository,
)

pytestmark = pytest.mark.integration


async def test_crypto_payments(app: FastAPI) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    async with app.router.lifespan_context(app), container() as scope:
        gateways = await scope.get(ICryptoGatewayService)
        first_gateway = await gateways.create(
            GatewayCreate(
                key="account-a",
                title="Account A",
                kind="provider-a",
                price_currency="USD",
                rial_rate=Decimal("550000"),
            )
        )
        second_gateway = await gateways.create(
            GatewayCreate(
                key="account-b",
                title="Account B",
                kind="provider-b",
                price_currency="EUR",
                rial_rate=Decimal("670000"),
            )
        )

        first = CryptoPaymentCreate(
            gateway_id=first_gateway.id,
            amount=4_180_000,
            price_amount=Decimal("7.123456789012345678901234"),
            price_currency="USD",
        )
        second = CryptoPaymentCreate(
            gateway_id=second_gateway.id,
            amount=5_690_000,
            price_amount=Decimal("8.50"),
            price_currency="EUR",
            pay_currency="USDT_TRON",
        )
        with pytest.raises(ValidationError) as invalid:
            CryptoPaymentCreate.model_validate(
                {**first.to_row(), "price_amount": 0.1}
            )
        assert invalid.value.errors()[0]["loc"] == ("price_amount",)

        url = "https://pay.example.test/invoices/42"
        repo = await scope.get(CryptoPaymentRepository)
        async with transaction():
            a = await repo.create(CryptoPaymentModel.from_dict(first.to_row()))
            b = await repo.create(
                CryptoPaymentModel.from_dict(second.to_row())
            )
            assert a.invoice_id is None
            assert a.status is CryptoPaymentStatus.PENDING
            assert b.pay_currency == second.pay_currency
            assert await repo.find_by_invoice(first.gateway_id, "42") is None

            linked = await repo.set_invoice(
                a.id, invoice_id="42", invoice_url=url
            )
            assert linked is not None
            assert linked.id == a.id
            assert linked.invoice_url == url
            assert linked.price_amount == first.price_amount
            assert (
                await repo.set_invoice(a.id, invoice_id="43", invoice_url=url)
                is None
            )
            linked_b = await repo.set_invoice(
                b.id, invoice_id="42", invoice_url=url
            )
            assert linked_b is not None
            assert linked_b.price_currency == "EUR"

        await gateways.update(
            first.gateway_id,
            GatewayUpdate(price_currency="GBP", rial_rate=Decimal("690000")),
        )
        with pytest.raises(ConflictException) as in_use:
            await gateways.remove(first.gateway_id)
        assert in_use.value.message_code == "crypto_gateway_in_use"

        with pytest.raises(IntegrityError):
            async with transaction():
                other = await repo.create(
                    CryptoPaymentModel.from_dict(first.to_row())
                )
                await repo.set_invoice(
                    other.id, invoice_id="42", invoice_url=url
                )

        async with transaction():
            stored = await repo.find_by_invoice(first.gateway_id, "42")
            assert stored is not None
            assert stored.amount == first.amount
            assert stored.price_amount == first.price_amount
            assert stored.price_currency == first.price_currency
            assert stored.pay_currency is None
            stored_b = await repo.find_by_invoice(second.gateway_id, "42")
            assert stored_b is not None
            assert stored_b.id == b.id
            assert await repo.find_by_invoice(first.gateway_id, "43") is None

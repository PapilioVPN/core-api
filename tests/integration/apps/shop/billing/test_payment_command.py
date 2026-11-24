"""Verify payment registration through its request-scoped command."""

from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from papilio.infra.db.transaction import transaction
from sqlalchemy.exc import IntegrityError

from src.apps.shop.billing.payments.app.interfaces.commands import (
    IPaymentCommand,
)
from src.apps.shop.billing.payments.domain.dtos.records import PaymentCreate
from src.apps.shop.billing.payments.domain.enums.records import PaymentStatus
from src.apps.shop.billing.payments.domain.models.records import PaymentModel
from src.apps.shop.billing.payments.infra.pg.repositories.crud import (
    PaymentRepository,
)
from src.apps.shop.billing.receipts.domain.enums.records import ReceiptStatus
from src.apps.shop.billing.receipts.infra.pg.repositories.crud import (
    ReceiptRepository,
)

pytestmark = pytest.mark.integration


async def test_create_payment(app: FastAPI) -> None:
    data = PaymentCreate(amount=4_000_000_005, image_url="/media/receipt.jpg")
    async with app.router.lifespan_context(app):
        container = cast(AsyncContainer, app.state.dishka_container)
        async with container() as scope:
            command = await scope.get(IPaymentCommand)
            payment = await command.create(data)

        async with container() as scope:
            payments = await scope.get(PaymentRepository)
            receipts = await scope.get(ReceiptRepository)
            try:
                stored = await payments.get_by_id(payment.id)
                assert stored is not None
                assert stored.amount == data.amount
                assert stored.status == PaymentStatus.PENDING
                assert stored.confirmed_at is None
                assert stored.receipt_id == payment.receipt_id

                receipt = await receipts.get_by_id(stored.receipt_id)
                assert receipt is not None
                assert receipt.image_url == data.image_url
                assert receipt.status == ReceiptStatus.PENDING
                assert receipt.amount is None and receipt.paid_at is None
                assert receipt.tracking_code is None
                assert receipt.reference_code is None
                assert receipt.bank_name is None
                assert receipt.source_last4 is None
                assert receipt.destination_last4 is None
            finally:
                async with transaction():
                    await payments.remove_by_id(payment.id)
                    await receipts.remove_by_id(payment.receipt_id)


async def test_payment_failure_rolls_back_receipt(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = PaymentCreate(amount=10_000, image_url="/media/rollback.jpg")
    async with app.router.lifespan_context(app):
        container = cast(AsyncContainer, app.state.dishka_container)
        async with container() as scope:
            payments = await scope.get(PaymentRepository)
            receipts = await scope.get(ReceiptRepository)
            payment_count = await payments.count()
            receipt_count = await receipts.count()

        async with container() as scope:
            payments = await scope.get(PaymentRepository)
            command = await scope.get(IPaymentCommand)
            create = payments.create

            async def create_twice(data: PaymentModel) -> PaymentModel:
                await create(data)
                duplicate = await create(data)
                return duplicate

            monkeypatch.setattr(payments, "create", create_twice)
            with pytest.raises(IntegrityError):
                await command.create(data)

        async with container() as scope:
            payments = await scope.get(PaymentRepository)
            receipts = await scope.get(ReceiptRepository)
            assert await payments.count() == payment_count
            assert await receipts.count() == receipt_count

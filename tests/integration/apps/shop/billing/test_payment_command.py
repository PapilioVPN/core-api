"""Verify payment registration through its request-scoped command."""

import json
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from papilio.infra.db.transaction import transaction
from papilio.infra.db.uow import PGUnitOfWork
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from src.apps.shop.billing.payments.app.interfaces.commands import (
    IPaymentCreateCommand,
)
from src.apps.shop.billing.payments.domain.dtos.records import PaymentCreate
from src.apps.shop.billing.payments.domain.enums.records import PaymentStatus
from src.apps.shop.billing.payments.domain.models.records import PaymentModel
from src.apps.shop.billing.payments.infra.pg.repositories.crud import (
    PaymentRepository,
)
from src.apps.shop.billing.receipts.domain.enums.records import ReceiptStatus
from src.apps.shop.billing.receipts.infra.broker.config import BrokerConfig
from src.apps.shop.billing.receipts.infra.pg.repositories.crud import (
    ReceiptRepository,
)
from src.bootstrap.outbox import pending

pytestmark = pytest.mark.integration


async def test_create_payment(app: FastAPI) -> None:
    data = PaymentCreate(amount=4_000_000_005, image_url="/media/receipt.jpg")
    async with app.router.lifespan_context(app):
        container = cast(AsyncContainer, app.state.dishka_container)
        async with container() as scope:
            command = await scope.get(IPaymentCreateCommand)
            payment = await command.create(data)
        receipt_id = payment.receipt_id
        assert receipt_id is not None

        async with container() as scope:
            payments = await scope.get(PaymentRepository)
            receipts = await scope.get(ReceiptRepository)
            uow = await scope.get(PGUnitOfWork)
            event_ids: list[int] = []
            try:
                stored = await payments.get_by_id(payment.id)
                assert stored is not None
                assert stored.amount == data.amount
                assert stored.status == PaymentStatus.PENDING
                assert stored.confirmed_at is None
                assert stored.receipt_id == receipt_id

                receipt = await receipts.get_by_id(receipt_id)
                assert receipt is not None
                assert receipt.image_url == data.image_url
                assert receipt.status == ReceiptStatus.PENDING
                assert receipt.amount is None and receipt.paid_at is None
                assert receipt.tracking_code is None
                assert receipt.reference_code is None
                assert receipt.bank_name is None
                assert receipt.source_last4 is None
                assert receipt.destination_last4 is None

                rows = await uow.execute(
                    select(pending.c.id, pending.c.payload).where(
                        pending.c.queue == BrokerConfig.created
                    )
                )
                for id, payload in rows.tuples():
                    event = json.loads(payload)["event"]
                    if event["receipt_id"] == receipt.id:
                        event_ids.append(id)
                        assert event == {"receipt_id": receipt.id}
                assert len(event_ids) == 1
            finally:
                async with transaction():
                    if event_ids:
                        await uow.execute(
                            delete(pending).where(pending.c.id.in_(event_ids))
                        )
                    await payments.remove_by_id(payment.id)
                    await receipts.remove_by_id(receipt_id)


async def test_payment_failure_rolls_back_receipt(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = PaymentCreate(amount=10_000, image_url="/media/rollback.jpg")
    events = select(func.count()).select_from(pending)
    async with app.router.lifespan_context(app):
        container = cast(AsyncContainer, app.state.dishka_container)
        async with container() as scope:
            payments = await scope.get(PaymentRepository)
            receipts = await scope.get(ReceiptRepository)
            uow = await scope.get(PGUnitOfWork)
            payment_count = await payments.count()
            receipt_count = await receipts.count()
            event_count = (await uow.execute(events)).scalar_one()

        async with container() as scope:
            payments = await scope.get(PaymentRepository)
            command = await scope.get(IPaymentCreateCommand)
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
            uow = await scope.get(PGUnitOfWork)
            assert await payments.count() == payment_count
            assert await receipts.count() == receipt_count
            assert (await uow.execute(events)).scalar_one() == event_count

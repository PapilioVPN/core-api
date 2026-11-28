"""Verify receipt requirements and storage for both card payment modes."""

from datetime import timedelta
from typing import Literal, cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from papilio.errors.exceptions import (
    ConflictException,
    NotFoundException,
    ValidationException,
)
from papilio.infra.db.transaction import transaction
from papilio.types.constants import INT64_MAX
from papilio.utils.dates import utc_now
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from src.apps.finance.card_to_card.payments.app.interfaces import commands
from src.apps.finance.card_to_card.payments.app.interfaces.services import (
    ICardPaymentService,
)
from src.apps.finance.card_to_card.payments.domain.dtos.records import (
    CardPaymentCreate,
)
from src.apps.finance.card_to_card.payments.domain.dtos.review import (
    CardPaymentReview,
)
from src.apps.finance.card_to_card.payments.domain.enums.records import (
    PaymentMode,
    PaymentStatus,
)
from src.apps.finance.card_to_card.payments.infra.pg.repositories.crud import (
    CardPaymentRepository,
)
from src.apps.finance.card_to_card.payments.routers.schemas.records import (
    CardPaymentOutput,
)
from src.apps.shop.banking.banks.domain.models.records import BankModel
from src.apps.shop.banking.banks.infra.pg.repositories.records import (
    BankRepository,
)
from src.apps.shop.banking.payment_cards.domain.models.records import (
    PaymentCardModel,
)
from src.apps.shop.banking.payment_cards.infra.pg.repositories.crud import (
    PaymentCardRepository,
)

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    "data",
    [
        {"amount": 100_000, "receipt_url": "/media/receipt.png"},
        {"card_id": 0, "amount": 100_000, "receipt_url": "/media/receipt.png"},
        {"card_id": 1, "amount": 100_000},
        {"card_id": 1, "amount": 0, "receipt_url": "/media/receipt.png"},
        {
            "card_id": 1,
            "amount": 100_000,
            "receipt_url": "file:///receipt.png",
        },
    ],
)
def test_create_requires_valid_amount_and_receipt(
    data: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        CardPaymentCreate.model_validate(data)


@pytest.mark.parametrize(
    ("status", "reason"),
    [
        (PaymentStatus.CONFIRMED, None),
        (PaymentStatus.REJECTED, "Amount mismatch"),
        (PaymentStatus.REJECTED, None),
    ],
)
async def test_manual_payment(
    app: FastAPI,
    status: Literal[PaymentStatus.CONFIRMED, PaymentStatus.REJECTED],
    reason: str | None,
) -> None:
    async with app.router.lifespan_context(app):
        container = cast(AsyncContainer, app.state.dishka_container)
        async with container() as scope:
            banks = await scope.get(BankRepository)
            cards = await scope.get(PaymentCardRepository)
            async with transaction():
                bank = await banks.create(
                    BankModel(code="finance_test", title="Finance Test")
                )
                card = await cards.create(
                    PaymentCardModel(
                        bank_id=bank.id,
                        card_number="0000000000000000",
                        holder_name="Test Holder",
                    )
                )
                card_id, bank_id = card.id, bank.id
            command = await scope.get(commands.IManualPaymentCommand)
            data = CardPaymentCreate(
                card_id=card_id,
                amount=4_000_000_005,
                receipt_url="/media/receipt.png",
                description="Manual transfer",
            )
            with pytest.raises(NotFoundException):
                await command.create(
                    CardPaymentCreate(
                        card_id=INT64_MAX,
                        amount=data.amount,
                        receipt_url=data.receipt_url,
                    )
                )
            payment = await command.create(data)
        assert payment.status is PaymentStatus.PENDING

        async with container() as scope:
            repo = await scope.get(CardPaymentRepository)
            service = await scope.get(ICardPaymentService)
            cards = await scope.get(PaymentCardRepository)
            banks = await scope.get(BankRepository)
            try:
                stored = await service.get_by_id(payment.id)
                assert stored.card_id == card_id
                assert stored.amount == data.amount
                assert stored.receipt_url == data.receipt_url
                assert stored.mode is PaymentMode.MANUAL
                assert stored.payable_amount is None
                assert stored.code is None
                assert stored.expires_at is None
                assert stored.description == data.description
                assert stored.created_at is not None
                assert stored.decided_at is None
                assert stored.rejection_reason is None
                with pytest.raises(IntegrityError):
                    async with transaction():
                        await cards.remove_by_id(card_id)
                with pytest.raises(ValidationException):
                    await service.review(
                        payment.id,
                        CardPaymentReview(
                            status=PaymentStatus.CONFIRMED, reason="Unexpected"
                        ),
                    )
                review = CardPaymentReview(status=status, reason=reason)
                with pytest.raises(NotFoundException):
                    await service.review(2**63 - 1, review)
                decided = await service.review(payment.id, review)
                assert decided.status is status
                decided_at = decided.decided_at
                assert decided_at is not None
                assert decided.rejection_reason == reason
                with pytest.raises(ConflictException):
                    await service.review(payment.id, review)
                async with container() as read_scope:
                    reader = await read_scope.get(ICardPaymentService)
                    stored = await reader.get_by_id(payment.id)
                assert stored.status is status
                assert stored.decided_at == decided_at
                assert stored.rejection_reason == reason
            finally:
                async with transaction():
                    await repo.remove_by_id(payment.id)
                    await cards.remove_by_id(card_id)
                    await banks.remove_by_id(bank_id)


async def test_auto_payment_record(app: FastAPI) -> None:
    expires_at = utc_now() + timedelta(minutes=30)
    async with app.router.lifespan_context(app):
        container = cast(AsyncContainer, app.state.dishka_container)
        async with container() as scope:
            banks = await scope.get(BankRepository)
            cards = await scope.get(PaymentCardRepository)
            repo = await scope.get(CardPaymentRepository)
            async with transaction():
                bank = await banks.create(
                    BankModel(code="auto_payments", title="Auto Payment Test")
                )
                card = await cards.create(
                    PaymentCardModel(
                        bank_id=bank.id,
                        card_number="0000000000000042",
                        holder_name="Auto Payment Test",
                    )
                )
            service = await scope.get(ICardPaymentService)
            payment = await service.create_auto(
                card_id=card.id,
                amount=4_000_199_995,
                payable_amount=4_000_200_007,
                code="0007",
                expires_at=expires_at,
            )
            try:
                async with container() as read_scope:
                    reader = await read_scope.get(ICardPaymentService)
                    stored = await reader.get_by_id(payment.id)
                assert stored.mode is PaymentMode.AUTO
                assert stored.status is PaymentStatus.PENDING
                assert stored.receipt_url is None
                assert stored.card_id == card.id
                assert stored.amount == 4_000_199_995
                assert stored.payable_amount == 4_000_200_007
                assert stored.code == "0007"
                assert stored.expires_at == expires_at
                assert CardPaymentOutput.from_obj(stored).receipt_url is None
            finally:
                async with transaction():
                    await repo.remove_by_id(payment.id)
                    await cards.remove_by_id(card.id)
                    await banks.remove_by_id(bank.id)

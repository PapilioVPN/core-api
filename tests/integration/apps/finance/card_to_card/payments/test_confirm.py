"""Verify automatic payment confirmation and its transactional event."""

from asyncio import gather
from datetime import timedelta
from json import loads
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.infra.db.transaction import transaction
from papilio.infra.db.uow import PGUnitOfWork
from papilio.utils.dates import utc_now
from sqlalchemy import delete, select

from src.apps.finance.banking.banks.domain.models.records import BankModel
from src.apps.finance.banking.banks.infra.pg.repositories.records import (
    BankRepository,
)
from src.apps.finance.banking.payment_cards.domain.models.records import (
    PaymentCardModel,
)
from src.apps.finance.banking.payment_cards.infra.pg.repositories.crud import (
    PaymentCardRepository,
)
from src.apps.finance.card_to_card.payments.app.interfaces import commands
from src.apps.finance.card_to_card.payments.app.interfaces.services import (
    ICardPaymentService,
)
from src.apps.finance.card_to_card.payments.domain.dtos.review import (
    CardPaymentReview,
)
from src.apps.finance.card_to_card.payments.domain.enums.records import (
    PaymentMode,
    PaymentStatus,
)
from src.apps.finance.card_to_card.payments.domain.models.records import (
    CardPaymentModel,
)
from src.apps.finance.card_to_card.payments.infra.pg.repositories.crud import (
    CardPaymentRepository,
)
from src.apps.finance.card_to_card.settings.app.interfaces.cache import (
    ITransferSettingsCache,
)
from src.apps.finance.card_to_card.settings.app.interfaces.services import (
    ITransferSettingsService,
)
from src.apps.finance.card_to_card.settings.domain.dtos.records import (
    TransferSettingsWrite,
)
from src.apps.finance.card_to_card.settings.domain.enums.records import (
    SettingsKey,
)
from src.apps.finance.card_to_card.settings.infra.pg.repositories.crud import (
    TransferSettingsRepository,
)
from src.apps.finance.card_to_card.transfers.app.interfaces.services import (
    ITransferService,
)
from src.apps.finance.card_to_card.transfers.domain.enums.records import (
    TransferSource,
)
from src.apps.finance.card_to_card.transfers.domain.models.records import (
    TransferModel,
)
from src.apps.finance.card_to_card.transfers.infra.pg.repositories import (
    crud as transfer_records,
)
from src.bootstrap.outbox import pending

pytestmark = pytest.mark.integration
CONFIRMED = "papiliovpn.finance.card_to_card.payment.confirmed.v1"


async def test_confirm_transfer(app: FastAPI, client: AsyncClient) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    now = utc_now()
    created_at = now - timedelta(hours=1)
    expires_at = now - timedelta(minutes=30)
    paid_at = now - timedelta(minutes=40)
    amount = 120_007

    async with container() as scope:
        command = await scope.get(commands.IConfirmTransferCommand)
        banks = await scope.get(BankRepository)
        cards = await scope.get(PaymentCardRepository)
        payments = await scope.get(CardPaymentRepository)
        transfers = await scope.get(ITransferService)
        async with transaction():
            bank = await banks.create(
                BankModel(code="confirm_bank", title="Confirmation Test")
            )
            card, other_card = [
                await cards.create(
                    PaymentCardModel(
                        bank_id=bank.id,
                        card_number=number,
                        holder_name="Test Holder",
                    )
                )
                for number in ("0000000000000065", "0000000000000073")
            ]
            terms = dict(
                card_id=card.id,
                amount=120_000,
                payable_amount=amount,
                code="0007",
                mode=PaymentMode.AUTO,
            )
            payment = await payments.create(
                CardPaymentModel.model_validate(
                    terms
                    | {"created_at": created_at, "expires_at": expires_at}
                )
            )
            later = await payments.create(
                CardPaymentModel.model_validate(
                    terms
                    | {
                        "created_at": now - timedelta(minutes=15),
                        "expires_at": now + timedelta(minutes=15),
                    }
                )
            )
            reviewed = await payments.create(
                CardPaymentModel.model_validate(
                    terms
                    | {
                        "payable_amount": amount + 2,
                        "code": "0009",
                        "created_at": created_at,
                        "expires_at": expires_at,
                    }
                )
            )
            transfer = await transfers.create(
                TransferModel(
                    amount=amount,
                    card_id=card.id,
                    transferred_at=paid_at,
                    created_at=now,
                    source=TransferSource.HOOK,
                    source_id=1,
                )
            )
            facts = transfer.model_dump(exclude={"id"})
            ignored = [
                await transfers.create(
                    TransferModel.model_validate(facts | change)
                )
                for change in (
                    {"source": TransferSource.ADMIN},
                    {"card_id": None},
                    {"card_id": other_card.id},
                    {"transferred_at": None},
                    {"transferred_at": expires_at},
                    {"transferred_at": created_at - timedelta(seconds=1)},
                    {"amount": amount + 1},
                    {"amount": amount + 2},
                )
            ]
        payment_id, later_id, transfer_id = payment.id, later.id, transfer.id
        reviewed_id = reviewed.id
        bank_id = bank.id
        card_ids = [card.id, other_card.id]
        skipped = [row.id for row in ignored]
        service = await scope.get(ICardPaymentService)
        await service.review(
            reviewed_id, CardPaymentReview(status=PaymentStatus.REJECTED)
        )
        assert await command.confirm(transfer_id) is None

    outbox_id = None
    try:
        async with container() as scope:
            settings = await scope.get(ITransferSettingsService)
            await settings.save(
                SettingsKey.GENERAL,
                TransferSettingsWrite(
                    auto_confirm=True, digits=4, window_minutes=30
                ),
            )
            command = await scope.get(commands.IConfirmTransferCommand)
            for id in skipped:
                assert await command.confirm(id) is None
            with pytest.raises(RuntimeError, match="rollback confirm"):
                async with transaction():
                    confirmed = await command.confirm(transfer_id)
                    assert confirmed is not None
                    raise RuntimeError("rollback confirm")

        async def confirm() -> CardPaymentModel | None:
            async with container() as scope:
                command = await scope.get(commands.IConfirmTransferCommand)
                result = await command.confirm(transfer_id)
                return result

        results = await gather(confirm(), confirm())
        assert [item.id for item in results if item is not None] == [
            payment_id
        ]
        async with container() as scope:
            payments = await scope.get(CardPaymentRepository)
            confirmed = await payments.get_by_id(payment_id)
            untouched = await payments.get_by_id(later_id)
            rejected = await payments.get_by_id(reviewed_id)
            assert confirmed is not None
            assert confirmed.status is PaymentStatus.CONFIRMED
            assert confirmed.transfer_id == transfer_id
            assert confirmed.decided_at is not None
            assert untouched is not None
            assert untouched.status is PaymentStatus.PENDING
            assert untouched.transfer_id is None
            assert rejected is not None
            assert rejected.status is PaymentStatus.REJECTED
            assert rejected.transfer_id is None
            unit = await scope.get(PGUnitOfWork)
            rows = await unit.execute(
                select(pending.c.id, pending.c.payload).where(
                    pending.c.queue == CONFIRMED
                )
            )
            event = rows.one()
            outbox_id = event.id
            assert loads(event.payload)["event"] == {"payment_id": payment_id}
    finally:
        async with container() as scope:
            repo = await scope.get(TransferSettingsRepository)
            cache = await scope.get(ITransferSettingsCache)
            payments = await scope.get(CardPaymentRepository)
            transfers = await scope.get(transfer_records.TransferRepository)
            cards = await scope.get(PaymentCardRepository)
            banks = await scope.get(BankRepository)
            unit = await scope.get(PGUnitOfWork)
            async with transaction():
                await payments.remove_by_ids(
                    [payment_id, later_id, reviewed_id]
                )
                await transfers.remove_by_ids([transfer_id, *skipped])
                await cards.remove_by_ids(card_ids)
                await banks.remove_by_id(bank_id)
                if outbox_id is not None:
                    await unit.execute(
                        delete(pending).where(pending.c.id == outbox_id)
                    )
                setting = await repo.find_by_key(SettingsKey.GENERAL)
                if setting is not None:
                    await repo.remove_by_id(setting.id)
            await cache.forget(SettingsKey.GENERAL)

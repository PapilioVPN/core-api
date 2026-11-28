"""Verify automatic payment orchestration and amount reservation."""

from asyncio import gather
from datetime import timedelta
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.errors.exceptions import ConflictException, ValidationException
from papilio.infra.db.transaction import transaction
from papilio.types.constants import INT64_MAX
from papilio.utils.dates import utc_now

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
from src.apps.finance.card_to_card.payments.domain.dtos.records import (
    AutoPaymentCreate,
)
from src.apps.finance.card_to_card.payments.domain.enums.records import (
    PaymentMode,
    PaymentStatus,
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

pytestmark = pytest.mark.integration


async def test_auto_payment_command(app: FastAPI, client: AsyncClient) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    try:
        async with container() as scope:
            command = await scope.get(commands.IAutoPaymentCommand)
            settings = await scope.get(ITransferSettingsService)
            banks = await scope.get(BankRepository)
            cards = await scope.get(PaymentCardRepository)
            async with transaction():
                bank = await banks.create(
                    BankModel(code="auto_issuance", title="Automatic Test")
                )
                first = await cards.create(
                    PaymentCardModel(
                        bank_id=bank.id,
                        card_number="0000000000000088",
                        holder_name="First Card",
                        allow_auto=True,
                    )
                )
                second = await cards.create(
                    PaymentCardModel(
                        bank_id=bank.id,
                        card_number="0000000000000099",
                        holder_name="Second Card",
                        allow_auto=False,
                    )
                )
                first_id, second_id = first.id, second.id
            with pytest.raises(ValidationException):
                await command.create(
                    AutoPaymentCreate(card_id=first_id, amount=120_000)
                )
            await settings.save(
                SettingsKey.GENERAL,
                TransferSettingsWrite(
                    auto_confirm=True, digits=4, window_minutes=30
                ),
            )
            with pytest.raises(ValidationException):
                await command.create(
                    AutoPaymentCreate(card_id=second_id, amount=120_000)
                )
            async with transaction():
                await cards.update_by_id(second_id, {"allow_auto": True})

        async with container() as scope:
            command = await scope.get(commands.IAutoPaymentCommand)
            start = utc_now()
            payment = await command.create(
                AutoPaymentCreate(card_id=first_id, amount=120_000)
            )
            another = await command.create(
                AutoPaymentCreate(card_id=second_id, amount=120_000)
            )
            assert payment.mode is PaymentMode.AUTO
            assert payment.status is PaymentStatus.PENDING
            assert payment.receipt_url is None
            assert payment.card_id == first_id
            assert payment.amount == 120_000
            assert payment.payable_amount == 120_001
            assert payment.code == "0001"
            assert payment.expires_at is not None
            assert start <= payment.expires_at - timedelta(minutes=30)
            assert payment.expires_at - timedelta(minutes=30) <= utc_now()
            assert another.payable_amount == 120_002
            assert another.code == "0002"
            with pytest.raises(ConflictException):
                await command.create(
                    AutoPaymentCreate(card_id=first_id, amount=INT64_MAX)
                )

        async def reserve(card_id: int) -> int:
            async with container() as scope:
                service = await scope.get(ICardPaymentService)
                row = await service.create_auto(
                    card_id=card_id,
                    amount=130_000,
                    payable_amount=130_001,
                    code="0001",
                    expires_at=utc_now() + timedelta(minutes=30),
                )
                return row.id

        results = await gather(
            reserve(first_id), reserve(second_id), return_exceptions=True
        )
        assert sum(isinstance(result, int) for result in results) == 1
        assert (
            sum(isinstance(result, ConflictException) for result in results)
            == 1
        )
    finally:
        async with container() as scope:
            repo = await scope.get(TransferSettingsRepository)
            cache = await scope.get(ITransferSettingsCache)
            async with transaction():
                setting = await repo.find_by_key(SettingsKey.GENERAL)
                if setting is not None:
                    await repo.remove_by_id(setting.id)
            await cache.forget(SettingsKey.GENERAL)

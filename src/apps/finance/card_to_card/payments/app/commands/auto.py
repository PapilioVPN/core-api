"""Check automatic payment eligibility and reserve a payable amount."""

from datetime import timedelta

from papilio.errors.exceptions import ConflictException, ValidationException
from papilio.infra.db.tools.decorators import transactional
from papilio.types.constants import INT64_MAX
from papilio.utils.dates import utc_now

from src.apps.finance.banking.payment_cards.app.interfaces.services import (
    IPaymentCardService,
)

from ....settings.app.interfaces.services import ITransferSettingsService
from ....settings.domain.enums.records import SettingsKey
from ...domain.dtos.records import AutoPaymentCreate
from ...domain.models.records import CardPaymentModel
from ..helpers.amount import assign_amount
from ..interfaces.services import ICardPaymentService


class AutoPaymentCommand:
    def __init__(
        self,
        settings: ITransferSettingsService,
        cards: IPaymentCardService,
        payments: ICardPaymentService,
    ) -> None:
        self.settings = settings
        self.cards = cards
        self.payments = payments

    @transactional
    async def create(self, data: AutoPaymentCreate) -> CardPaymentModel:
        """Issue a pending payment with an unused exact transfer amount.

        Args:
            data: Validated destination card ID and base amount in rials.

        Returns:
            The stored payment including its exact amount, code and expiry.

        Raises:
            NotFoundException: No card has the supplied identity.
            ValidationException: Auto payments are disabled globally or
                unavailable on the selected card.
            ConflictException: No amount is free or a concurrent issue
                reserved the chosen amount first.
        """
        settings = await self.settings.find(SettingsKey.GENERAL)
        if (
            settings is None
            or not settings.auto_confirm
            or settings.window_minutes is None
        ):
            raise ValidationException(
                message="Automatic card payments are disabled.",
                message_code="card_auto_disabled",
                loc=["mode"],
            )
        card = await self.cards.get_by_id(data.card_id)
        if not card.is_active or not card.allow_auto:
            raise ValidationException(
                message="The destination card does not accept auto payments.",
                message_code="card_auto_unavailable",
                loc=["card_id"],
            )

        digits = settings.digits
        expires_at = utc_now() + timedelta(minutes=settings.window_minutes)
        first = data.amount + 1
        last = min(data.amount + 10**digits - 1, INT64_MAX)
        reserved = (
            await self.payments.reserved_amounts(
                first=first, last=last, expires_at=expires_at
            )
            if first <= last
            else set()
        )
        terms = assign_amount(first, last, digits, reserved)
        if terms is None:
            raise ConflictException(
                message="No transfer amount is available in this range.",
                message_code="card_amount_unavailable",
                unique_dict={"amount": data.amount},
            )
        payable_amount, code = terms
        payment = await self.payments.create_auto(
            card_id=card.id,
            amount=data.amount,
            payable_amount=payable_amount,
            code=code,
            expires_at=expires_at,
        )
        return payment

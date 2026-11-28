"""Check the card destination and register a manual payment."""

from papilio.infra.db.tools.decorators import transactional

from src.apps.finance.banking.payment_cards.app.interfaces.services import (
    IPaymentCardService,
)

from ...domain.dtos.records import CardPaymentCreate
from ...domain.models.records import CardPaymentModel
from ..interfaces.services import ICardPaymentService


class ManualPaymentCommand:
    def __init__(
        self, cards: IPaymentCardService, payments: ICardPaymentService
    ) -> None:
        self.cards = cards
        self.payments = payments

    @transactional
    async def create(self, data: CardPaymentCreate) -> CardPaymentModel:
        """Store a manual payment for an existing destination card.

        Args:
            data: Validated card ID, amount, receipt and optional note.

        Returns:
            The stored pending manual payment.

        Raises:
            NotFoundException: The selected destination card is missing.
        """
        await self.cards.get_by_id(data.card_id)
        payment = await self.payments.create(data)
        return payment

"""Register a transfer against its customer and receiving card."""

from papilio.infra.db.tools.decorators import transactional

from src.apps.shop.banking.payment_cards.app.interfaces.services import (
    ICardCRUD,
)
from src.apps.shop.customers.profiles.app.interfaces.services import (
    IProfileCRUD,
)

from ...domain.dtos.records import PaymentCreate
from ...domain.models.records import PaymentModel
from ..interfaces.services import IPaymentCRUD


class PaymentCommand:
    def __init__(
        self, payments: IPaymentCRUD, profiles: IProfileCRUD, cards: ICardCRUD
    ) -> None:
        """Bind payment registration and the current request's lookups.

        Args:
            payments: Owning payment record service.
            profiles: Authoritative customer service.
            cards: Authoritative destination card service.

        Returns:
            None.
        """
        self.payments = payments
        self.profiles = profiles
        self.cards = cards

    @transactional
    async def create(self, data: PaymentCreate) -> PaymentModel:
        """Record a transfer for manual review.

        Args:
            data: Customer, destination card, rial amount and receipt details.

        Returns:
            The pending payment with its recorded destination.

        Raises:
            NotFoundException: The customer or card is absent.
        """
        await self.profiles.get_by_id(data.customer_id)
        card = await self.cards.get_by_id(data.card_id)
        payment = await self.payments.create(
            PaymentModel(
                customer_id=data.customer_id,
                card_id=card.id,
                bank_id=card.bank_id,
                card_last4=card.card_number[-4:],
                amount=data.amount,
                reference=data.reference,
                paid_at=data.paid_at,
            )
        )
        return payment

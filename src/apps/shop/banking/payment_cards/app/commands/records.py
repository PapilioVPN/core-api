"""Resolve the issuer of a receiving card before storing its number."""

from papilio.errors.exceptions import ValidationException
from papilio.infra.db.tools.decorators import transactional
from pydantic_core import MISSING

from src.apps.shop.banking.banks.app.interfaces.queries import IBankQuery

from ...domain.dtos.records import CardCreate, CardUpdate
from ...domain.models.records import PaymentCardModel
from ..interfaces.services import ICardCRUD


class CardCommand:
    def __init__(self, cards: ICardCRUD, banks: IBankQuery) -> None:
        """Bind card configuration to its request.

        Args:
            cards: Owning card record service.
            banks: Authoritative offline bank lookup.

        Returns:
            None.
        """
        self.cards = cards
        self.banks = banks

    @transactional
    async def create(self, data: CardCreate) -> PaymentCardModel:
        """Register a destination card and its matching active issuer.

        Args:
            data: Validated card number, holder and payment configuration.

        Returns:
            The stored card with its resolved issuer identity.

        Raises:
            ValidationException: No active issuer and prefix match the number.
            ConflictException: This card number is already registered.
        """
        bank_id = await self._bank_id(data.card_number)
        card = await self.cards.create(
            PaymentCardModel(
                bank_id=bank_id,
                card_number=data.card_number,
                holder_name=data.holder_name,
                is_active=data.is_active,
                allow_manual=data.allow_manual,
                allow_auto=data.allow_auto,
            )
        )
        return card

    @transactional
    async def update(self, id: int, data: CardUpdate) -> PaymentCardModel:
        """Apply settings changes and resolve the issuer of any new number.

        Args:
            id: Stored card identity.
            data: Validated partial changes with explicit presence.

        Returns:
            The updated card. Omitted fields keep their stored values.
        """
        changes = data.to_row()
        if data.card_number is not MISSING:
            bank_id = await self._bank_id(data.card_number)
            changes = {**changes, "bank_id": bank_id}
        card = await self.cards.update(id, PaymentCardModel.patch(**changes))
        return card

    async def _bank_id(self, number: str) -> int:
        """Resolve the active issuer of a card.

        Args:
            number: Locally validated 16-digit card number.

        Returns:
            The matching active bank identity.

        Raises:
            ValidationException: The bank or prefix is absent or inactive.
        """
        match = await self.banks.find_by_prefix(number[:8])
        if (
            match is None
            or not match.is_prefix_active
            or not match.bank.is_active
        ):
            raise ValidationException(
                message="No active bank matches this card number.",
                message_code="unknown_card_issuer",
                loc=["body", "card_number"],
            )
        return match.bank.id

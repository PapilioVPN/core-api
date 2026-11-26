"""Resolve the active issuer of a validated card number."""

from papilio.errors.exceptions import ValidationException

from src.apps.shop.banking.banks.app.interfaces.queries import IBankQuery

MAX_PREFIX_LENGTH = 8


class CardIssuerService:
    def __init__(self, banks: IBankQuery) -> None:
        """Bind the offline bank lookup."""
        self.banks = banks

    async def resolve(self, number: str) -> int:
        """Resolve the active issuer of a card.

        Args:
            number: Locally validated 16-digit card number.

        Returns:
            The matching active bank identity.

        Raises:
            ValidationException: The bank or prefix is absent or inactive.
        """
        match = await self.banks.find_by_prefix(number[:MAX_PREFIX_LENGTH])
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

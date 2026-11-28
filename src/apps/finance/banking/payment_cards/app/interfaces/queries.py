"""Check or select eligible receiving cards."""

from typing import Protocol

from ...domain.enums.records import PaymentMode
from ...domain.models.records import PaymentCardModel


class ICardPickQuery(Protocol):
    async def available(self, mode: PaymentMode) -> bool:
        """Report whether a card can accept the requested payment mode."""
        ...

    async def pick(self, mode: PaymentMode) -> PaymentCardModel | None:
        """Return one eligible card or None when no card is configured."""
        ...

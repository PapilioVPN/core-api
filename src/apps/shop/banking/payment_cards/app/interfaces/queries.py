"""Receiving card selection for the checkout capability."""

from typing import Protocol

from ...domain.enums.records import PaymentMode
from ...domain.models.records import PaymentCardModel


class ICardPickQuery(Protocol):
    async def pick(self, mode: PaymentMode) -> PaymentCardModel | None:
        """Return one eligible card or None when no card is configured."""
        ...

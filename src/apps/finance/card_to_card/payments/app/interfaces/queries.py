"""Panel payment list query."""

from typing import Protocol

from papilio.schemas.results import PagedType

from ...domain.dtos.records import CardPaymentList
from ...domain.models.records import CardPaymentModel


class ICardPaymentQuery(Protocol):
    async def list(
        self, data: CardPaymentList
    ) -> PagedType[CardPaymentModel]: ...

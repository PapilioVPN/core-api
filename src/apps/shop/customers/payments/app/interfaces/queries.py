"""Search contract for the panel payment queue."""

from typing import Protocol

from papilio.schemas.results import PagedType

from ...domain.dtos.search import PaymentSearch
from ...domain.models.records import PaymentModel


class IPaymentSearch(Protocol):
    async def search(self, data: PaymentSearch) -> PagedType[PaymentModel]: ...

"""Payment reads for the administrator panel."""

from typing import Protocol

from papilio.schemas.results import PagedType

from ...domain.dtos.search import PaymentSearch
from ...domain.models.records import PaymentModel
from ...domain.results.details import PaymentDetail


class IPaymentQuery(Protocol):
    async def get_by_id(self, id: int) -> PaymentDetail: ...


class IPaymentSearchQuery(Protocol):
    async def search(self, data: PaymentSearch) -> PagedType[PaymentModel]: ...

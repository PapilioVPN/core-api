"""Independent inputs for the three trusted preview commands."""

from typing import Protocol

from src.apps.shop.products.volume_ranges.domain.dtos.quote import QuoteInput

from ...domain.dtos.records import TopupInput
from ...domain.models.records import Invoice


class IInvoiceCommand(Protocol):
    async def topup(self, customer_id: int, data: TopupInput) -> Invoice: ...

    async def catalog(self, customer_id: int, catalog_id: int) -> Invoice: ...

    async def range(
        self, customer_id: int, service_id: int, data: QuoteInput
    ) -> Invoice: ...

"""Read previews by trusted customer identity."""

from typing import Protocol
from uuid import UUID

from ...domain.models.records import Invoice


class IInvoiceService(Protocol):
    async def get(self, customer_id: int, id: UUID) -> Invoice: ...

"""Receipt record operations for the panel and bot adapters."""

from typing import Protocol

from ...domain.dtos.records import ReceiptCreate
from ...domain.models.records import ReceiptModel


class IReceiptService(Protocol):
    async def create(self, data: ReceiptCreate) -> ReceiptModel: ...

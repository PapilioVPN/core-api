"""Receipt record operations used by Billing."""

from typing import Protocol

from ...domain.models.records import ReceiptModel


class IReceiptService(Protocol):
    async def create(self, data: ReceiptModel) -> ReceiptModel: ...

    async def get_by_id(self, id: int) -> ReceiptModel: ...

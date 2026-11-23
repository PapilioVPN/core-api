"""Persistence and reads for customer receipts."""

from typing import Protocol

from ...domain.models.records import ReceiptModel


class IReceiptCRUD(Protocol):
    async def create(self, data: ReceiptModel) -> ReceiptModel: ...

    async def get_by_id(self, id: int) -> ReceiptModel: ...

    async def check_image(self, url: str) -> None: ...

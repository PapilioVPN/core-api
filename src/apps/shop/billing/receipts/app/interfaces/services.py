"""Receipt record operations used by Billing."""

from typing import Protocol

from ...domain.dtos.review import ReceiptReview
from ...domain.models.records import ReceiptModel


class IReceiptService(Protocol):
    async def create(self, data: ReceiptModel) -> ReceiptModel: ...

    async def review(self, id: int, data: ReceiptReview) -> ReceiptModel: ...

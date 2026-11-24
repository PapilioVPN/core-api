"""Receipt record operations used by Billing."""

from typing import Protocol

from ...domain.enums.extraction import ExtractionStatus
from ...domain.models.records import ReceiptModel
from ...domain.results.extraction import ReceiptFields


class IReceiptService(Protocol):
    async def create(self, data: ReceiptModel) -> ReceiptModel: ...

    async def get_by_id(self, id: int) -> ReceiptModel: ...

    async def find_by_id(self, id: int) -> ReceiptModel | None: ...

    async def save_extraction(
        self, id: int, status: ExtractionStatus, fields: ReceiptFields
    ) -> None: ...

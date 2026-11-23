"""Registration through the owning receipt upload command."""

from typing import Protocol

from anyio.abc import ByteReceiveStream

from ...domain.dtos.records import ImageType, ReceiptCreate
from ...domain.models.records import ReceiptModel


class IReceiptCommand(Protocol):
    async def create(
        self,
        customer_id: int,
        data: ReceiptCreate,
        source: ByteReceiveStream,
        *,
        mime_type: ImageType,
    ) -> ReceiptModel: ...

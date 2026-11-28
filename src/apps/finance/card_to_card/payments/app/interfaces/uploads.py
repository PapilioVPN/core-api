"""Upload a receipt image independently of payment registration."""

from typing import Protocol

from anyio.abc import ByteReceiveStream

from src.apps.core.storage.files.domain.results.uploads import FileUploadResult

from ...domain.dtos.uploads import ReceiptUpload


class IReceiptUpload(Protocol):
    async def upload(
        self, source: ByteReceiveStream, data: ReceiptUpload, *, max_bytes: int
    ) -> FileUploadResult: ...

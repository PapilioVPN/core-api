"""Receipt image operations shared by trusted upload and read entrypoints."""

from contextlib import AbstractAsyncContextManager
from typing import Protocol

from anyio.abc import ByteReceiveStream

from ...domain.enums.images import ImageFormat


class IReceiptImages(Protocol):
    async def upload(
        self, source: ByteReceiveStream, format: ImageFormat, *, max_bytes: int
    ) -> str:
        """Store a validated image privately and return its content digest."""
        ...

    def open(
        self, format: ImageFormat, digest: str
    ) -> AbstractAsyncContextManager[ByteReceiveStream]:
        """Open an authorized image stream for the enclosing response."""
        ...

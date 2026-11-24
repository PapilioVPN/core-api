"""Adapt an operation-owned S3 response to a bounded AnyIO stream."""

from typing import TYPE_CHECKING

from anyio import ClosedResourceError, EndOfStream
from anyio.abc import ByteReceiveStream

if TYPE_CHECKING:
    from aiobotocore.response import StreamingBody


class S3ReadStream(ByteReceiveStream):
    def __init__(self, body: "StreamingBody") -> None:
        self._body = body
        self._closed = False

    async def receive(self, max_bytes: int = 65536) -> bytes:
        """Read up to max_bytes with the SDK's native backpressure.

        Raises:
            ValueError: The requested bound is not positive.
            ClosedResourceError: The response has been closed.
            EndOfStream: The object has no more bytes.
        """
        if max_bytes < 1:
            raise ValueError("max_bytes must be positive")
        if self._closed:
            raise ClosedResourceError
        data = await self._body.read(min(max_bytes, 1024 * 1024))
        if not data:
            raise EndOfStream
        return data

    async def aclose(self) -> None:
        """Close this adapter. Its caller owns the borrowed SDK response."""
        self._closed = True

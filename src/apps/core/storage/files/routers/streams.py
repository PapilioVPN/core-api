"""Adapt native HTTP body chunks to the app's bounded byte-stream contract."""

from collections.abc import AsyncGenerator

from anyio import ClosedResourceError, EndOfStream
from anyio.abc import ByteReceiveStream
from fastapi import HTTPException


class RequestBodyStream(ByteReceiveStream):
    def __init__(
        self, chunks: AsyncGenerator[bytes], *, max_bytes: int
    ) -> None:
        """Borrow a native request stream without preloading its body.

        Args:
            chunks: Request.stream() generator; no multipart/form parsing.
            max_bytes: Server-owned actual byte limit, independent of headers.
        Returns:
            None. At most the current ASGI body block is retained.
        """
        self.chunks = chunks
        self.max_bytes = max_bytes
        self.received = 0
        self.pending = memoryview(b"")
        self.closed = False

    async def receive(self, max_bytes: int = 65536) -> bytes:
        """Consume no more than the requested byte bound with backpressure.

        Args:
            max_bytes: Positive maximum returned bytes.
        Returns:
            Nonempty bytes from the current body position.
        Raises:
            HTTPException: Actual request body exceeds the server limit (413).
            EndOfStream: The native request body has ended.
            ClosedResourceError: This adapter has been closed.
            ValueError: The requested receive bound is not positive.
        """
        if max_bytes < 1:
            raise ValueError("max_bytes must be positive")
        if self.closed:
            raise ClosedResourceError
        while not self.pending:
            try:
                chunk = await anext(self.chunks)
            except StopAsyncIteration as error:
                raise EndOfStream from error
            self.received += len(chunk)
            if self.received > self.max_bytes:
                raise HTTPException(413, "File exceeds the upload byte limit")
            self.pending = memoryview(chunk)
        result = self.pending[:max_bytes].tobytes()
        self.pending = self.pending[max_bytes:]
        return result

    async def aclose(self) -> None:
        """Release the current block and close the borrowed request iterator.

        Args:
            None.
        Returns:
            None. Socket ownership remains with the native ASGI server.
        """
        self.closed = True
        self.pending = memoryview(b"")
        await self.chunks.aclose()

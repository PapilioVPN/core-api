"""Borrow an HTTP request body as a bounded byte stream."""

from collections.abc import AsyncGenerator

from anyio import ClosedResourceError, EndOfStream
from anyio.abc import ByteReceiveStream


class RequestBodyStream(ByteReceiveStream):
    def __init__(self, chunks: AsyncGenerator[bytes]) -> None:
        self.chunks = chunks
        self.pending = memoryview(b"")
        self.closed = False

    async def receive(self, max_bytes: int = 65536) -> bytes:
        if max_bytes < 1:
            raise ValueError("max_bytes must be positive")
        if self.closed:
            raise ClosedResourceError
        while not self.pending:
            try:
                self.pending = memoryview(await anext(self.chunks))
            except StopAsyncIteration as error:
                raise EndOfStream from error
        chunk = self.pending[:max_bytes].tobytes()
        self.pending = self.pending[max_bytes:]
        return chunk

    async def aclose(self) -> None:
        self.closed = True
        self.pending = memoryview(b"")
        await self.chunks.aclose()

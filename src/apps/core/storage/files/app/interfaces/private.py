"""Private file operations for authorized application consumers."""

from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager
from typing import Protocol

from anyio.abc import ByteReceiveStream

from src.apps.core.storage.files.domain.results.staging import StagedFile


class IPrivateFiles(Protocol):
    async def upload(
        self,
        source: ByteReceiveStream,
        directory: str,
        *,
        max_bytes: int,
        validator: Callable[[StagedFile], Awaitable[None]],
    ) -> str:
        """Store bytes under a trusted directory and return their digest."""
        ...

    def open(
        self, directory: str, digest: str
    ) -> AbstractAsyncContextManager[ByteReceiveStream]:
        """Open a private file by its directory and validated digest."""
        ...

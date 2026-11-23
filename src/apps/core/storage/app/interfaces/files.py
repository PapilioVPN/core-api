"""Upload and resolve files through the owning storage service."""

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Protocol

from anyio.abc import ByteReceiveStream


class IFileStorage(Protocol):
    async def upload(
        self,
        source: ByteReceiveStream,
        *,
        base_url: str,
        suffix: str,
        validate: Callable[[Path], Awaitable[None]],
    ) -> str: ...

    async def get_path(self, name: str) -> Path: ...

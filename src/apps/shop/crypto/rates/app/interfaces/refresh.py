"""Queue a manual refresh without waiting for the worker."""

from typing import Protocol


class IRateRefreshPublisher(Protocol):
    async def enqueue(self) -> str: ...

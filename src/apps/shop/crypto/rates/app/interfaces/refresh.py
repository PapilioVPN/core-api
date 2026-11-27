"""Queue a manual refresh without waiting for the worker."""

from typing import Protocol

from ...domain.results.records import RateFailure


class IRateRefreshPublisher(Protocol):
    async def enqueue(self) -> str | RateFailure: ...

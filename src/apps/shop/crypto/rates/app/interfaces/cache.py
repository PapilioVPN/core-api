"""Store the latest successful rate by currency."""

from typing import Protocol

from ...domain.models.records import Rate
from ...domain.results.records import RateFailure


class IRateCache(Protocol):
    async def save(self, data: Rate) -> Rate | RateFailure: ...

    async def find(self, currency: str) -> Rate | RateFailure | None: ...

    async def find_all(self) -> list[Rate] | RateFailure: ...

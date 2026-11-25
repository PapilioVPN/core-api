"""Store the latest successful rate by currency."""

from typing import Protocol

from ...domain.models.records import Rate


class IRateCache(Protocol):
    async def save(self, data: Rate) -> Rate: ...

    async def find(self, currency: str) -> Rate | None: ...

"""Persistence phase used by rate refresh."""

from typing import Protocol

from ...domain.models.records import CryptoRateModel


class IRateRefreshExecution(Protocol):
    async def complete(self, data: CryptoRateModel) -> CryptoRateModel: ...

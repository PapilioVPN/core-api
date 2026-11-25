"""Persistence operations for shared pricing rates."""

from typing import Protocol

from ...domain.models.records import CryptoRateModel


class ICryptoRateService(Protocol):
    async def save(self, data: CryptoRateModel) -> CryptoRateModel: ...

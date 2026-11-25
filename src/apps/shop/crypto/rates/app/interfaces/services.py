"""Persistence operations for shared pricing rates."""

from datetime import datetime, timedelta
from typing import Protocol

from ...domain.models.records import CryptoRateModel
from ...domain.results.conversion import Conversion


class ICryptoRateService(Protocol):
    async def save(self, data: CryptoRateModel) -> CryptoRateModel: ...

    async def find_by_currency(
        self, currency: str
    ) -> CryptoRateModel | None: ...


class IConversionService(Protocol):
    def to_usd(
        self,
        amount: int,
        rate: CryptoRateModel | None,
        *,
        now: datetime,
        max_age: timedelta,
    ) -> Conversion: ...

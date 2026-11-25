"""Conversion operations for shared pricing rates."""

from datetime import datetime, timedelta
from typing import Protocol

from ...domain.models.records import Rate
from ...domain.results.conversion import Conversion


class IConversionService(Protocol):
    def to_usd(
        self,
        amount: int,
        rate: Rate | None,
        *,
        now: datetime,
        max_age: timedelta,
    ) -> Conversion: ...

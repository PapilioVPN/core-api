"""Conversion operations for shared pricing rates."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Protocol

from ...domain.models.records import Rate
from ...domain.results.conversion import Conversion, RialConversion
from ...domain.results.records import RateFailure


class IConversionService(Protocol):
    def to_usd(
        self,
        amount: int,
        rate: Rate | None,
        *,
        now: datetime,
        max_age: timedelta,
    ) -> Conversion | RateFailure: ...

    def to_rial(
        self,
        amount: Decimal,
        rate: Rate | None,
        *,
        now: datetime,
        max_age: timedelta,
    ) -> RialConversion | RateFailure: ...

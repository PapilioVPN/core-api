"""The Wallex USDT market input used by rate refresh."""

from decimal import Decimal
from typing import Protocol

from ...domain.results.records import RateFailure


class IWallexRate(Protocol):
    async def read(self) -> Decimal | RateFailure:
        """Return the last USDT trade price in tomans."""
        ...

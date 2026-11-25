"""The Wallex USDT market input used by rate refresh."""

from decimal import Decimal
from typing import Protocol


class IWallexRate(Protocol):
    async def read(self) -> Decimal:
        """Return the last USDT trade price in tomans."""
        ...

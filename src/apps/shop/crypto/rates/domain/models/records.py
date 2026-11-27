"""The latest market observation for one pricing currency."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

USD = "USD"
WALLEX_USDT = "wallex_usdt"


@dataclass(frozen=True, slots=True)
class Rate:
    currency: str
    rial_rate: Decimal
    source: str
    fetched_at: datetime

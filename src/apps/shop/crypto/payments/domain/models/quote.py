"""A prepared invoice price before any provider call."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal


@dataclass(frozen=True, slots=True)
class Quote:
    amount: Decimal
    currency: Literal["IRR", "USD"]
    rate: Decimal | None = None

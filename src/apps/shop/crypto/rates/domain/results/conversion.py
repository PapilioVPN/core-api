"""Converted amount and the exact rate used."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Conversion:
    amount: Decimal
    rial_rate: Decimal

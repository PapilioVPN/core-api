"""Converted amount and the exact rate used."""

from dataclasses import dataclass
from decimal import Decimal

USD_CENT = Decimal("0.01")
RIAL_UNIT = Decimal("1")
CONVERSION_PRECISION = 64


@dataclass(frozen=True, slots=True)
class Conversion:
    amount: Decimal
    rial_rate: Decimal


@dataclass(frozen=True, slots=True)
class RialConversion:
    amount: int
    rial_rate: Decimal

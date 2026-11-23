"""The priced selection returned to the storefront."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RangeQuote:
    range_id: int
    volume_bytes: int
    days: int | None
    price: int

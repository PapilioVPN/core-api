"""Receipt facts supported by the first extraction pass."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReceiptFields:
    amount: int | None = None
    tracking_code: str | None = None
    reference_code: str | None = None

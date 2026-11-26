"""Verified payment references and normalized invoice evidence."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Settlement:
    payment_id: int
    invoice_id: str
    reference: str


@dataclass(frozen=True, slots=True)
class PaidInvoice:
    settlement: Settlement
    amount: Decimal
    currency: str

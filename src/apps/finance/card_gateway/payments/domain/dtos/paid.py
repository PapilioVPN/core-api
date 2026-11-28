"""A verified provider notification normalized to whole rials."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class PaidTransfer:
    slug: str
    attempt_code: str
    base_amount: int
    paid_amount: int
    sent_at: datetime


@dataclass(frozen=True, slots=True)
class PaidDelivery:
    gateway_id: int
    delivery_id: str
    transfer: PaidTransfer

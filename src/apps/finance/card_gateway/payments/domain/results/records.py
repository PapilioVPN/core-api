"""Hosted payment details for the status read."""

from dataclasses import dataclass
from datetime import datetime

from ..enums.records import PaymentStatus


@dataclass(frozen=True, slots=True)
class PaymentDetails:
    id: int
    gateway_id: int
    status: PaymentStatus
    amount: int
    paid_amount: int | None
    attempt_code: str | None
    pay_url: str | None
    expires_at: datetime | None
    confirmed_at: datetime | None

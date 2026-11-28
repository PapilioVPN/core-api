"""Expose the local status and recorded payment evidence."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput

from ...domain.enums.records import PaymentStatus


class PaymentOutput(BaseOutput):
    id: int
    gateway_id: int
    status: PaymentStatus
    amount: int
    paid_amount: int | None
    attempt_code: str | None
    pay_url: str | None
    expires_at: datetime | None
    confirmed_at: datetime | None

"""Expose provider-issued identifiers and confirmed bank evidence."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput

from ...domain.enums.records import LinkStatus


class PaymentOutput(BaseOutput):
    id: int
    gateway_id: int
    amount: int
    description: str
    status: LinkStatus
    reference: str | None
    tracking_code: str | None
    pay_url: str | None
    confirmed_at: datetime | None
    created_at: datetime

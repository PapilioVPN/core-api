"""Payment details and review facts visible to the panel."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput

from ...domain.enums.records import PaymentStatus


class PaymentOutput(BaseOutput):
    id: int
    customer_id: int
    card_id: int | None
    bank_id: int
    card_last4: str
    amount: int
    reference: str
    paid_at: datetime | None
    status: PaymentStatus
    reviewer_id: int | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime

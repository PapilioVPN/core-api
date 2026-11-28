"""Card payment details available to authorized Finance operators."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput

from ...domain.enums.records import PaymentMode, PaymentStatus


class CardPaymentOutput(BaseOutput):
    id: int
    card_id: int
    amount: int
    mode: PaymentMode
    payable_amount: int | None
    code: str | None
    expires_at: datetime | None
    receipt_url: str | None
    description: str | None
    status: PaymentStatus
    transfer_id: int | None
    decided_at: datetime | None
    rejection_reason: str | None
    created_at: datetime
    updated_at: datetime

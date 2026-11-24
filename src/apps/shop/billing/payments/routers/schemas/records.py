"""Payment fields returned to authorized Shop operators."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput

from src.apps.shop.billing.receipts.routers.schemas.records import (
    ReceiptOutput,
)

from ...domain.enums.records import PaymentStatus


class PaymentOutput(BaseOutput):
    id: int
    receipt_id: int
    amount: int
    status: PaymentStatus
    confirmed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PaymentReviewOutput(PaymentOutput):
    rejection_reason: str | None


class PaymentDetailOutput(BaseOutput):
    payment: PaymentReviewOutput
    receipt: ReceiptOutput

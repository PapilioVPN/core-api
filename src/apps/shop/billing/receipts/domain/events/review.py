"""Receipt lifecycle event payloads."""

from papilio.schemas.inputs import BaseDTO


class ReceiptCreated(BaseDTO):
    receipt_id: int


class ReceiptReviewed(BaseDTO):
    receipt_id: int
    payment_id: int
    actor_id: int


class ReceiptApproved(ReceiptReviewed):
    pass


class ReceiptRejected(ReceiptReviewed):
    reason: str | None = None

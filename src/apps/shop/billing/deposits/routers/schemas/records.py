"""The stored bank report returned by the hook and panel."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput


class DepositOutput(BaseOutput):
    id: int
    amount: int
    paid_at: datetime | None
    payment_id: int | None
    created_at: datetime

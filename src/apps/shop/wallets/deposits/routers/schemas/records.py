"""Wallet top-up requests returned to authorized operators."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput


class DepositOutput(BaseOutput):
    id: int
    customer_id: int
    amount: int
    created_at: datetime

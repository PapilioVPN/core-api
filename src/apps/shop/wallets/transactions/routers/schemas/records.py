"""Wallet movement details returned to authorized operators."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput

from ...domain.enums.records import Direction


class TransactionOutput(BaseOutput):
    id: int
    customer_id: int
    direction: Direction
    amount: int
    balance_before: int
    balance_after: int
    description: str | None
    created_at: datetime

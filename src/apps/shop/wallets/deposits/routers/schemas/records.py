"""Wallet top-up invoices returned to authorized operators."""

from datetime import datetime
from math import ceil
from uuid import UUID

from papilio.schemas.outputs import BaseOutput
from papilio.utils.dates import utc_now
from pydantic import computed_field


class DepositOutput(BaseOutput):
    id: UUID
    customer_id: int
    amount: int
    created_at: datetime
    expires_at: datetime

    @computed_field
    @property
    def expires_in(self) -> int:
        """Return the seconds remaining when this response is serialized."""
        remaining = (self.expires_at - utc_now()).total_seconds()
        return max(0, ceil(remaining))

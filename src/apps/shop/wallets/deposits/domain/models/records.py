"""An expiring invoice for a wallet top-up."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class DepositInvoice:
    id: UUID
    customer_id: int
    amount: int
    created_at: datetime
    expires_at: datetime

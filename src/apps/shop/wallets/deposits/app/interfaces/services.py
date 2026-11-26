"""Operations on expiring wallet top-up invoices."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from ...domain.models.records import DepositInvoice, DepositPayment


class IWalletDepositService(Protocol):
    async def create(
        self,
        customer_id: int,
        amount: int,
        payment: DepositPayment,
        *,
        created_at: datetime | None = None,
    ) -> DepositInvoice: ...

    async def get_by_id(
        self, customer_id: int, id: UUID
    ) -> DepositInvoice: ...

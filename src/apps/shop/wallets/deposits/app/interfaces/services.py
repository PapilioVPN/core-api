"""Operations on expiring wallet top-up invoices."""

from typing import Protocol
from uuid import UUID

from ...domain.models.records import DepositInvoice


class IWalletDepositService(Protocol):
    async def create(
        self, customer_id: int, amount: int
    ) -> DepositInvoice: ...

    async def get_by_id(
        self, customer_id: int, id: UUID
    ) -> DepositInvoice: ...

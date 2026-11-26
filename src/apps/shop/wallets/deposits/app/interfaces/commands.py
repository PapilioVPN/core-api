"""Issue an initial wallet top-up invoice."""

from typing import Protocol

from ...domain.dtos.records import DepositCreate
from ...domain.models.records import DepositInvoice


class IWalletDepositCommand(Protocol):
    async def issue(
        self, customer_id: int, data: DepositCreate
    ) -> DepositInvoice: ...

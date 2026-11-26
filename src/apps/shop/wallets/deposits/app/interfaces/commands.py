"""Issue an initial wallet top-up invoice."""

from typing import Protocol

from ...domain.dtos.records import CardDeposit, PlisioDeposit
from ...domain.models.records import DepositInvoice


class ICardInvoiceCommand(Protocol):
    async def issue(
        self, customer_id: int, data: CardDeposit
    ) -> DepositInvoice: ...


class IPlisioInvoiceCommand(Protocol):
    async def issue(
        self, customer_id: int, data: PlisioDeposit
    ) -> DepositInvoice: ...

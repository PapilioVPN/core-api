"""Payment record operations used by Billing."""

from typing import Protocol

from ...domain.models.records import PaymentModel


class IPaymentService(Protocol):
    async def create(self, data: PaymentModel) -> PaymentModel: ...

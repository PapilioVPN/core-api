"""Payment record operations used by Billing."""

from datetime import datetime
from typing import Protocol

from ...domain.enums.records import PaymentStatus
from ...domain.models.records import PaymentModel


class IPaymentService(Protocol):
    async def create(self, data: PaymentModel) -> PaymentModel: ...

    async def review(
        self,
        receipt_id: int,
        status: PaymentStatus,
        *,
        confirmed_at: datetime | None,
    ) -> PaymentModel: ...

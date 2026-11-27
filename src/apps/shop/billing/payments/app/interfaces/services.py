"""Payment record operations used by Billing."""

from datetime import datetime
from typing import Protocol

from ...domain.enums.records import PaymentStatus
from ...domain.models.records import PaymentModel


class IPaymentService(Protocol):
    async def create(self, data: PaymentModel) -> PaymentModel: ...

    async def get_by_id(self, id: int) -> PaymentModel: ...

    async def attach_receipt(
        self, id: int, receipt_id: int
    ) -> PaymentModel | None: ...

    async def create_auto(
        self, data: PaymentModel, digits: int
    ) -> PaymentModel | None: ...

    async def confirm_auto(
        self, amount: int, *, since: datetime, until: datetime
    ) -> PaymentModel | None: ...

    async def review(
        self,
        id: int,
        status: PaymentStatus,
        *,
        confirmed_at: datetime | None,
        reason: str | None = None,
    ) -> PaymentModel: ...


class IPaymentRegistrationService(Protocol):
    async def create_manual(
        self, amount: int, image_url: str
    ) -> PaymentModel: ...

    async def reserve_auto(self, amount: int) -> PaymentModel: ...

"""Payment registration and manual review contracts."""

from typing import Protocol

from ...domain.dtos.records import PaymentCreate
from ...domain.models.records import PaymentModel


class IPaymentCommand(Protocol):
    async def create(self, data: PaymentCreate) -> PaymentModel: ...


class IPaymentReviewCommand(Protocol):
    async def confirm(self, id: int) -> PaymentModel: ...

    async def reject(
        self, id: int, *, reason: str | None = None
    ) -> PaymentModel: ...

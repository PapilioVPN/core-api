"""Register a pending payment for an owning business flow."""

from typing import Protocol

from ...domain.dtos.records import PaymentCreate
from ...domain.models.records import PaymentModel


class IPaymentCommand(Protocol):
    async def create(self, data: PaymentCreate) -> PaymentModel: ...

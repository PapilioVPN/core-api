"""Independent Billing payment write operations."""

from datetime import datetime
from typing import Protocol

from ...domain.dtos.records import PaymentCreate
from ...domain.models.records import PaymentModel


class IPaymentCreateCommand(Protocol):
    async def create(self, data: PaymentCreate) -> PaymentModel: ...


class IPaymentAttachReceiptCommand(Protocol):
    async def attach_receipt(
        self, id: int, image_url: str
    ) -> PaymentModel: ...


class IPaymentConfirmCommand(Protocol):
    async def confirm(self, id: int) -> PaymentModel: ...


class IPaymentAutoConfirmCommand(Protocol):
    async def confirm_auto(
        self, amount: int, *, since: datetime, until: datetime
    ) -> PaymentModel | None: ...


class IPaymentRejectCommand(Protocol):
    async def reject(
        self, id: int, *, reason: str | None = None
    ) -> PaymentModel: ...

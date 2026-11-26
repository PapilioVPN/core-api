"""Payment registration and manual review contracts."""

from datetime import datetime
from typing import Protocol

from ...domain.dtos.records import PaymentCreate
from ...domain.models.records import PaymentModel


class IPaymentCommand(Protocol):
    async def create(self, data: PaymentCreate) -> PaymentModel: ...

    async def create_manual(
        self, amount: int, image_url: str
    ) -> PaymentModel: ...

    async def attach_receipt(
        self, id: int, image_url: str
    ) -> PaymentModel: ...

    async def reserve_auto(
        self, amount: int, digits: int, *, receipt_id: int | None = None
    ) -> PaymentModel: ...


class IPaymentReviewCommand(Protocol):
    async def confirm(self, id: int) -> PaymentModel: ...

    async def confirm_auto(
        self, amount: int, *, since: datetime, until: datetime
    ) -> PaymentModel | None: ...

    async def reject(
        self, id: int, *, reason: str | None = None
    ) -> PaymentModel: ...

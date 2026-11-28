"""Hosted payment status, notification records and confirmation."""

from typing import Protocol

from ...domain.dtos.paid import PaidDelivery, PaidTransfer
from ...domain.models.records import PaymentModel
from ...domain.results.records import PaymentDetails


class IPaymentService(Protocol):
    async def get_by_id(self, id: int) -> PaymentDetails: ...

    async def confirm(
        self, gateway_id: int, transfer: PaidTransfer
    ) -> PaymentModel | None: ...


class IDeliveryService(Protocol):
    async def record(self, delivery: PaidDelivery) -> int | None: ...

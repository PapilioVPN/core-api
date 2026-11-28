"""Confirmation command for authenticated provider notifications."""

from typing import Protocol

from ...domain.dtos.paid import PaidDelivery
from ...domain.models.records import PaymentModel


class IConfirmPaymentCommand(Protocol):
    async def confirm(self, delivery: PaidDelivery) -> PaymentModel | None: ...

"""Prepare a local crypto payment and freeze its price."""

from datetime import timedelta
from typing import Protocol

from ...domain.dtos.records import PaymentCreate
from ...domain.models.records import CryptoPaymentModel


class IPaymentCreateCommand(Protocol):
    async def create(self, data: PaymentCreate) -> CryptoPaymentModel: ...


class IPaymentQuoteCommand(Protocol):
    async def quote(
        self, id: int, *, max_age: timedelta
    ) -> CryptoPaymentModel: ...

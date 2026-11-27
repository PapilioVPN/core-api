"""Prepare a local crypto payment and freeze its price."""

from datetime import timedelta
from typing import Protocol

from src.apps.shop.crypto.rates.domain.results.records import RateFailure

from ...domain.dtos.records import PaymentCreate
from ...domain.models.records import CryptoPaymentModel
from ...domain.results.settlement import Settlement


class IPaymentCreateCommand(Protocol):
    async def create(self, data: PaymentCreate) -> CryptoPaymentModel: ...


class IPaymentQuoteCommand(Protocol):
    async def quote(
        self, id: int, *, max_age: timedelta
    ) -> CryptoPaymentModel | RateFailure: ...


class IPaymentConfirmCommand(Protocol):
    async def confirm(self, data: Settlement) -> CryptoPaymentModel | None: ...

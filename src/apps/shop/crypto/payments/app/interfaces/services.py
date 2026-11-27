"""Operations owned by the cryptocurrency payment service."""

from datetime import datetime, timedelta
from typing import Protocol

from pydantic import JsonValue

from src.apps.shop.crypto.gateways.domain.results.configs import ConfigFailure
from src.apps.shop.crypto.rates.domain.results.records import RateFailure

from ...domain.models.quote import Quote
from ...domain.models.records import CryptoPaymentModel
from ...domain.results.invoice import Invoice
from ...domain.results.records import PaymentFailure
from ...domain.results.settlement import Settlement


class ICryptoPaymentService(Protocol):
    async def create(self, data: CryptoPaymentModel) -> CryptoPaymentModel: ...

    async def get_by_id(self, id: int) -> CryptoPaymentModel: ...

    async def claim(
        self, *, now: datetime, before: datetime, limit: int
    ) -> tuple[int, ...]: ...

    async def set_quote(
        self, id: int, data: Quote
    ) -> CryptoPaymentModel | None: ...

    async def set_invoice(
        self, id: int, data: Invoice
    ) -> CryptoPaymentModel | None: ...

    async def confirm(
        self,
        id: int,
        invoice_id: str,
        settlement_id: str,
        confirmed_at: datetime,
    ) -> CryptoPaymentModel | None: ...


class IPaymentPricingService(Protocol):
    async def price(
        self, payment: CryptoPaymentModel, *, max_age: timedelta
    ) -> Quote | RateFailure | ConfigFailure: ...


class IPaymentNotificationService(Protocol):
    async def verify(
        self, gateway_id: int, data: dict[str, JsonValue], signature: str
    ) -> Settlement | ConfigFailure | PaymentFailure | None: ...

"""Short storage phases for payment confirmation."""

from typing import Protocol

from src.apps.shop.crypto.gateways.domain.results.configs import ConfigFailure

from ...domain.models.records import CryptoPaymentModel
from ...domain.results.check import PlisioCheck
from ...domain.results.records import PaymentFailure


class IPaymentCheckExecution(Protocol):
    async def claim(self, *, limit: int, delay: int) -> tuple[int, ...]: ...

    async def prepare(
        self, id: int
    ) -> PlisioCheck | CryptoPaymentModel | ConfigFailure | PaymentFailure: ...

    async def complete(
        self, id: int, invoice_id: str, settlement_id: str
    ) -> CryptoPaymentModel: ...

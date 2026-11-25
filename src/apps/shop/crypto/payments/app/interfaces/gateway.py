"""Gateway contract used by the payment command."""

from typing import Protocol

from src.apps.shop.crypto.gateways.domain.dtos.configs import ConfigWrite

from ...domain.models.records import CryptoPaymentModel
from ...domain.results.gateway import (
    GatewayInvoice,
    GatewayNotice,
    GatewayPayment,
)


class ICryptoPaymentGateway(Protocol):
    async def issue(
        self, account: ConfigWrite, payment: CryptoPaymentModel
    ) -> GatewayInvoice: ...

    def verify(
        self, account: ConfigWrite, body: bytes, signature: str | None
    ) -> GatewayNotice: ...

    async def read(
        self, account: ConfigWrite, payment_id: str
    ) -> GatewayPayment: ...

"""Gateway contract used by the payment command."""

from typing import Protocol

from src.apps.shop.crypto.gateways.domain.models.records import (
    CryptoGatewayModel,
)

from ...domain.models.records import CryptoPaymentModel
from ...domain.results.gateway import (
    GatewayInvoice,
    GatewayNotice,
    GatewayPayment,
)


class ICryptoPaymentGateway(Protocol):
    def price_decimals(self, gateway: CryptoGatewayModel) -> int: ...

    async def issue(
        self, gateway: CryptoGatewayModel, payment: CryptoPaymentModel
    ) -> GatewayInvoice: ...

    def verify(
        self, gateway: CryptoGatewayModel, body: bytes, signature: str
    ) -> GatewayNotice: ...

    async def read(
        self, gateway: CryptoGatewayModel, payment_id: str
    ) -> GatewayPayment: ...

"""Operations owned by crypto payment persistence."""

from typing import Protocol

from ...domain.dtos.records import CryptoPaymentCreate
from ...domain.enums.records import CryptoPaymentStatus
from ...domain.models.records import CryptoPaymentModel
from ...domain.results.gateway import GatewayInvoice


class ICryptoPaymentService(Protocol):
    async def create(
        self, data: CryptoPaymentCreate
    ) -> CryptoPaymentModel: ...

    async def get_by_id(self, id: int) -> CryptoPaymentModel: ...

    async def get_by_invoice(
        self, gateway_id: int, invoice_id: str
    ) -> CryptoPaymentModel: ...

    async def set_invoice(
        self, id: int, invoice: GatewayInvoice
    ) -> CryptoPaymentModel: ...

    async def settle(
        self, id: int, status: CryptoPaymentStatus, provider_payment_id: str
    ) -> CryptoPaymentModel: ...

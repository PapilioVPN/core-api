"""Operations owned by the cryptocurrency payment service."""

from typing import Protocol

from ...domain.models.quote import Quote
from ...domain.models.records import CryptoPaymentModel
from ...domain.results.invoice import Invoice


class ICryptoPaymentService(Protocol):
    async def create(self, data: CryptoPaymentModel) -> CryptoPaymentModel: ...

    async def get_by_id(self, id: int) -> CryptoPaymentModel: ...

    async def set_quote(
        self, id: int, data: Quote
    ) -> CryptoPaymentModel | None: ...

    async def set_invoice(
        self, id: int, data: Invoice
    ) -> CryptoPaymentModel | None: ...

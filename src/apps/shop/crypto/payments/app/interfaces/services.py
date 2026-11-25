"""Operations owned by the cryptocurrency payment service."""

from typing import Protocol

from ...domain.models.quote import Quote
from ...domain.models.records import CryptoPaymentModel


class ICryptoPaymentService(Protocol):
    async def create(self, data: CryptoPaymentModel) -> CryptoPaymentModel: ...

    async def get_by_id(self, id: int) -> CryptoPaymentModel: ...

    async def set_quote(
        self, id: int, data: Quote
    ) -> CryptoPaymentModel | None: ...

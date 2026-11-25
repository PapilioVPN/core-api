"""Operations owned by the cryptocurrency payment service."""

from typing import Protocol

from ...domain.models.records import CryptoPaymentModel


class ICryptoPaymentService(Protocol):
    async def create(self, data: CryptoPaymentModel) -> CryptoPaymentModel: ...

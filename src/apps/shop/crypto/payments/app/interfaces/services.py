"""Operations owned by the cryptocurrency payment service."""

from typing import Protocol

from ...domain.dtos.records import PaymentCreate
from ...domain.models.records import CryptoPaymentModel


class ICryptoPaymentService(Protocol):
    async def create(self, data: PaymentCreate) -> CryptoPaymentModel: ...

"""Application operations for issuing and settling a crypto payment."""

from typing import Protocol

from ...domain.dtos.records import PaymentIssue
from ...domain.models.records import CryptoPaymentModel


class ICryptoPaymentCommand(Protocol):
    async def issue(self, data: PaymentIssue) -> CryptoPaymentModel: ...

    async def receive(
        self, gateway_id: int, body: bytes, signature: str | None = None
    ) -> CryptoPaymentModel | None: ...

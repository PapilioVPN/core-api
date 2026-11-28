"""Read authenticated Variza deliveries without HTTP dependencies."""

from typing import Protocol

from pydantic import SecretStr

from ...domain.dtos.paid import PaidDelivery, PaidTransfer


class IVarizaWebhookCodec(Protocol):
    def valid_signature(
        self, body: bytes, signature: str, secret: SecretStr
    ) -> bool: ...

    def read_paid(self, body: bytes) -> PaidTransfer | None: ...


class IVarizaWebhookService(Protocol):
    async def read(
        self,
        gateway_id: int,
        delivery_id: str,
        body: bytes,
        signature: str | None,
    ) -> PaidDelivery | None: ...

"""Verification requested by a provider redirect."""

from typing import Protocol

from ....gateways.domain.enums.records import GatewayKind
from ...domain.models.records import PaymentModel


class IVerifyCallbackCommand(Protocol):
    async def verify(
        self, kind: GatewayKind, reference: str
    ) -> PaymentModel | None: ...

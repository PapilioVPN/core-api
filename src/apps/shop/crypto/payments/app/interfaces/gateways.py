"""Authenticated invoice operations offered by Plisio."""

from typing import Protocol

from pydantic import JsonValue

from src.apps.shop.crypto.gateways.domain.dtos.configs import PlisioConfig

from ...domain.results.check import Operation
from ...domain.results.invoice import Invoice, NowPaymentsIssue, PlisioIssue
from ...domain.results.settlement import PaidInvoice


class IPlisioGateway(Protocol):
    async def issue(self, data: PlisioIssue) -> Invoice: ...

    async def read(self, config: PlisioConfig, id: str) -> Operation: ...


class INowPaymentsGateway(Protocol):
    async def issue(self, data: NowPaymentsIssue) -> Invoice: ...


class INowPaymentsNotification(Protocol):
    def decode(
        self,
        gateway_id: int,
        data: dict[str, JsonValue],
        signature: str,
        secret: str,
    ) -> PaidInvoice | None: ...

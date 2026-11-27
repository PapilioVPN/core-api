"""Authenticated invoice operations offered by Plisio."""

from typing import Protocol

from pydantic import JsonValue

from src.apps.shop.crypto.gateways.domain.dtos.configs import PlisioConfig

from ...domain.results.check import Operation
from ...domain.results.invoice import Invoice, NowPaymentsIssue, PlisioIssue
from ...domain.results.records import PaymentFailure
from ...domain.results.settlement import PaidInvoice


class IPlisioGateway(Protocol):
    async def issue(self, data: PlisioIssue) -> Invoice | PaymentFailure: ...

    async def read(
        self, config: PlisioConfig, id: str
    ) -> Operation | PaymentFailure: ...


class INowPaymentsGateway(Protocol):
    async def issue(
        self, data: NowPaymentsIssue
    ) -> Invoice | PaymentFailure: ...


class INowPaymentsNotification(Protocol):
    def decode(
        self,
        data: dict[str, JsonValue],
        signature: str,
        secret: str,
    ) -> PaidInvoice | PaymentFailure | None: ...

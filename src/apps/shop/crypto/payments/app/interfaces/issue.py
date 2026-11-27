"""The provider call and short storage phases for hosted issuance."""

from typing import Protocol

from src.apps.shop.crypto.gateways.domain.results.configs import ConfigFailure

from ...domain.results.invoice import Invoice, NowPaymentsIssue, PlisioIssue
from ...domain.results.records import PaymentFailure


class IPaymentIssuePipeline(Protocol):
    async def issue(
        self, id: int, *, expire_minutes: int | None = None
    ) -> Invoice | ConfigFailure | PaymentFailure: ...


class IPaymentIssueExecution(Protocol):
    async def prepare(
        self, id: int
    ) -> PlisioIssue | NowPaymentsIssue | Invoice | ConfigFailure: ...

    async def complete(self, id: int, data: Invoice) -> Invoice: ...

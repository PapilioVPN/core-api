"""The provider call and short storage phases for hosted issuance."""

from typing import Protocol

from ...domain.results.invoice import Invoice, PlisioIssue


class IPaymentIssuePipeline(Protocol):
    async def issue(
        self, id: int, *, expire_minutes: int | None = None
    ) -> Invoice: ...


class IPaymentIssueExecution(Protocol):
    async def prepare(self, id: int) -> PlisioIssue | Invoice: ...

    async def complete(self, id: int, data: Invoice) -> Invoice: ...

"""Issue a hosted invoice after releasing database resources."""

from dataclasses import replace

from ...domain.results.invoice import Invoice, NowPaymentsIssue, PlisioIssue
from ..interfaces.gateways import INowPaymentsGateway, IPlisioGateway
from ..interfaces.issue import IPaymentIssueExecution


class PaymentIssuePipeline:
    def __init__(
        self,
        execution: IPaymentIssueExecution,
        plisio: IPlisioGateway,
        nowpayments: INowPaymentsGateway,
    ) -> None:
        """Bind the storage phases and hosted gateway adapters."""
        self.execution = execution
        self.plisio = plisio
        self.nowpayments = nowpayments

    async def issue(
        self, id: int, *, expire_minutes: int | None = None
    ) -> Invoice:
        """Return the saved invoice or issue one at the frozen price.

        Args:
            id: A previously committed and quoted payment.
            expire_minutes: Hosted payment window in minutes, if supplied.

        Returns:
            The provider invoice identity and hosted URL.

        Raises:
            InvoiceUnavailable: The provider did not return a usable invoice.
            ConflictException: The payment is not ready or the invoice changed.
        """
        prepared = await self.execution.prepare(id)
        match prepared:
            case Invoice():
                invoice = prepared
            case PlisioIssue():
                request = replace(prepared, expire_minutes=expire_minutes)
                invoice = await self.plisio.issue(request)
            case NowPaymentsIssue():
                invoice = await self.nowpayments.issue(prepared)
        if not isinstance(prepared, Invoice):
            invoice = await self.execution.complete(id, invoice)
        return invoice

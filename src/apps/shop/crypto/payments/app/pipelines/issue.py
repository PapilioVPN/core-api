"""Issue a hosted invoice after releasing database resources."""

from ...domain.results.invoice import Invoice, PlisioIssue
from ..interfaces.issue import IPaymentIssueExecution, IPlisioGateway


class PaymentIssuePipeline:
    def __init__(
        self, execution: IPaymentIssueExecution, plisio: IPlisioGateway
    ) -> None:
        """Bind the storage phases and the Plisio adapter."""
        self.execution = execution
        self.plisio = plisio

    async def issue(self, id: int) -> Invoice:
        """Return the saved invoice or issue one at the frozen price.

        Args:
            id: A previously committed and quoted payment.

        Returns:
            The provider invoice identity and hosted URL.

        Raises:
            InvoiceUnavailable: Plisio did not return a usable invoice.
            ConflictException: The payment is not ready or the invoice changed.
        """
        prepared = await self.execution.prepare(id)
        if isinstance(prepared, PlisioIssue):
            data = await self.plisio.issue(prepared)
            invoice = await self.execution.complete(id, data)
        else:
            invoice = prepared
        return invoice

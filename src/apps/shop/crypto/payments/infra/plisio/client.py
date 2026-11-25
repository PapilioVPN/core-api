"""Issue hosted invoices through Papilio's shared HTTP pool."""

from httpx import HTTPError
from papilio.infra.http.gateway import BaseGateway
from pydantic import ValidationError

from ...domain.errors import InvoiceUnavailable
from ...domain.results.invoice import Invoice, PlisioIssue
from .schemas import InvoiceResponse


class PlisioGateway(BaseGateway):
    async def issue(self, data: PlisioIssue) -> Invoice:
        """Create or recover the hosted invoice for the same merchant order.

        Args:
            data: Original merchant order ID, exact frozen price and account.

        Returns:
            The provider invoice identity and hosted URL.

        Raises:
            InvoiceUnavailable: The request failed or the reply was unusable.
        """
        order = str(data.payment_id)
        try:
            response = await self.client.get(
                f"{data.config.api_url}/invoices/new",
                headers=self.headers_of(),
                params={
                    "api_key": data.config.api_key.get_secret_value(),
                    "order_number": order,
                    "order_name": order,
                    "source_currency": data.currency,
                    "source_amount": format(data.amount, "f"),
                    "return_existing": "true",
                },
                follow_redirects=False,
            )
            response.raise_for_status()
            result = InvoiceResponse.model_validate_json(response.content)
        except (HTTPError, ValidationError):
            raise InvoiceUnavailable() from None
        return Invoice(id=result.data.txn_id, url=str(result.data.invoice_url))

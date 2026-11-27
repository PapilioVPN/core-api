"""Issue hosted USD invoices through NOWPayments."""

from decimal import Decimal
from typing import Annotated

from httpx import HTTPError
from papilio.infra.http.connection import HTTPConnection
from papilio.infra.http.gateway import BaseGateway
from pydantic import AnyUrl, BaseModel, Field, UrlConstraints, ValidationError

from ...domain.results.invoice import Invoice, NowPaymentsIssue
from ...domain.results.records import PaymentFailure


class InvoiceResponse(BaseModel):
    id: Annotated[
        str, Field(min_length=1, max_length=64, coerce_numbers_to_str=True)
    ]
    invoice_url: Annotated[
        AnyUrl, UrlConstraints(allowed_schemes=["https"], host_required=True)
    ]


class NowPaymentsGateway(BaseGateway):
    def __init__(self, connection: HTTPConnection) -> None:
        """Borrow the shared application HTTP pool."""
        super().__init__(connection)

    async def issue(self, data: NowPaymentsIssue) -> Invoice | PaymentFailure:
        """Create a hosted invoice for the committed local order.

        Args:
            data: Local payment, frozen USD amount and gateway settings.

        Returns:
            The hosted invoice or an unavailable result.
        """
        amount = float(data.amount)
        callback = data.config.callback_url
        invoice: Invoice | PaymentFailure = PaymentFailure.INVOICE_UNAVAILABLE
        if Decimal(str(amount)) == data.amount and callback is not None:
            try:
                response = await self.client.post(
                    f"{data.config.api_url}/invoice",
                    headers=self.headers_of(
                        {"x-api-key": data.config.api_key.get_secret_value()}
                    ),
                    json={
                        "price_amount": amount,
                        "price_currency": "usd",
                        "order_id": str(data.payment_id),
                        "ipn_callback_url": str(callback),
                    },
                    follow_redirects=False,
                )
                response.raise_for_status()
                result = InvoiceResponse.model_validate_json(response.content)
            except (HTTPError, ValidationError):
                pass
            else:
                invoice = Invoice(id=result.id, url=str(result.invoice_url))
        return invoice

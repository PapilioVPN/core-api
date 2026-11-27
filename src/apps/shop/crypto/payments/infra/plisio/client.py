"""Issue and inspect hosted invoices through Papilio's shared HTTP pool."""

from decimal import Decimal
from json import loads

from httpx import HTTPError
from papilio.infra.http.gateway import BaseGateway
from pydantic import ValidationError

from src.apps.shop.crypto.gateways.domain.dtos.configs import PlisioConfig

from ...domain.results.check import Operation, OperationStatus
from ...domain.results.invoice import Invoice, PlisioIssue
from ...domain.results.records import PaymentFailure
from .schemas import InvoiceResponse, OperationResponse

_STATUSES = {
    "completed": OperationStatus.COMPLETED,
    "cancelled duplicate": OperationStatus.REPLACED,
}


class PlisioGateway(BaseGateway):
    async def issue(self, data: PlisioIssue) -> Invoice | PaymentFailure:
        """Create or recover the hosted invoice for the same merchant order.

        Args:
            data: Original merchant order ID, exact frozen price and account.

        Returns:
            Hosted invoice details, or an unavailable result.
        """
        order = str(data.payment_id)
        params = {
            "api_key": data.config.api_key.get_secret_value(),
            "order_number": order,
            "order_name": order,
            "source_currency": data.currency,
            "source_amount": format(data.amount, "f"),
            "return_existing": "true",
        }
        if data.expire_minutes is not None:
            params["expire_min"] = str(data.expire_minutes)
        try:
            response = await self.client.get(
                f"{data.config.api_url}/invoices/new",
                headers=self.headers_of(),
                params=params,
                follow_redirects=False,
            )
            response.raise_for_status()
            result = InvoiceResponse.model_validate_json(response.content)
        except (HTTPError, ValidationError):
            invoice = PaymentFailure.INVOICE_UNAVAILABLE
        else:
            invoice = Invoice(
                id=result.data.txn_id, url=str(result.data.invoice_url)
            )
        return invoice

    async def read(
        self, config: PlisioConfig, id: str
    ) -> Operation | PaymentFailure:
        """Read authenticated facts about a Plisio invoice.

        Args:
            config: The original issuing account settings.
            id: A validated provider invoice ID.

        Returns:
            Exact invoice evidence, or an unavailable result.
        """
        try:
            response = await self.client.get(
                f"{config.api_url}/operations/{id}",
                headers=self.headers_of(),
                params={"api_key": config.api_key.get_secret_value()},
                follow_redirects=False,
            )
            response.raise_for_status()
            result = OperationResponse.model_validate(
                loads(response.content, parse_float=Decimal)
            )
        except (HTTPError, ValueError):
            operation: Operation | PaymentFailure = (
                PaymentFailure.CHECK_UNAVAILABLE
            )
        else:
            data = result.data
            operation = PaymentFailure.CHECK_UNAVAILABLE
            if data.id == id:
                params = data.params
                order = params.order_number if params is not None else None
                operation = Operation(
                    id=data.id,
                    status=_STATUSES.get(data.status, OperationStatus.OTHER),
                    parent_id=data.parent_id,
                    child_ids=data.child_ids or (),
                    order_id=str(order) if order is not None else None,
                    quote_amount=params.source_amount
                    if params is not None
                    else None,
                    quote_currency=params.source_currency if params else None,
                    expected=data.sum,
                    received=data.actual_sum,
                )
        return operation

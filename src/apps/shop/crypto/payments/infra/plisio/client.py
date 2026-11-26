"""Issue and inspect hosted invoices through Papilio's shared HTTP pool."""

from decimal import Decimal
from json import loads

from httpx import HTTPError
from papilio.infra.http.gateway import BaseGateway
from pydantic import ValidationError

from src.apps.shop.crypto.gateways.domain.dtos.configs import PlisioConfig

from ...domain.errors import CheckUnavailable, InvoiceUnavailable
from ...domain.results.check import Operation
from ...domain.results.invoice import Invoice, PlisioIssue
from .schemas import InvoiceResponse, OperationResponse


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
            raise InvoiceUnavailable() from None
        return Invoice(id=result.data.txn_id, url=str(result.data.invoice_url))

    async def read(self, config: PlisioConfig, id: str) -> Operation:
        """Read authenticated facts about a Plisio invoice.

        Args:
            config: The original issuing account settings.
            id: A validated provider invoice ID.

        Returns:
            The invoice, with exact fiat and transfer amounts when present.

        Raises:
            CheckUnavailable: The reply was unusable or for a different ID.
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
            raise CheckUnavailable() from None
        data = result.data
        if data.id != id:
            raise CheckUnavailable()
        params = data.params
        order = params.order_number if params is not None else None
        return Operation(
            id=data.id,
            status=data.status,
            parent_id=data.parent_id,
            child_ids=data.child_ids or (),
            order_id=str(order) if order is not None else None,
            quote_amount=params.source_amount if params is not None else None,
            quote_currency=params.source_currency
            if params is not None
            else None,
            expected=data.sum,
            received=data.actual_sum,
        )

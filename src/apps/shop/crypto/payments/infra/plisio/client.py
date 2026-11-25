"""Issue hosted Plisio invoices and obtain authenticated payment facts."""

from decimal import Decimal
from json import loads

from httpx import HTTPError
from papilio.errors.exceptions import UnAuthorizedException
from papilio.infra.http.gateway import BaseGateway
from pydantic import BaseModel

from src.apps.shop.crypto.gateways.domain.dtos.configs import ConfigWrite

from ...domain.enums.records import CryptoPaymentStatus
from ...domain.errors import GatewayUnavailable
from ...domain.models.records import CryptoPaymentModel
from ...domain.results.gateway import (
    GatewayInvoice,
    GatewayNotice,
    GatewayPayment,
)
from .schemas import InvoiceOut, OperationOut, Success
from .signature import decode_notice

STATES = {
    "completed": CryptoPaymentStatus.CONFIRMED,
    "underpaid": CryptoPaymentStatus.PARTIAL,
}


class PlisioGateway(BaseGateway):
    async def _get[T: BaseModel](
        self,
        account: ConfigWrite,
        path: str,
        schema: type[Success[T]],
        **params: str,
    ) -> T:
        endpoint = str(account.api_url).rstrip("/")
        try:
            response = await self.get(
                f"{endpoint}/{path}",
                params={
                    **params,
                    "api_key": account.api_key.get_secret_value(),
                },
            )
            response.raise_for_status()
            result = schema.model_validate(
                loads(response.content, parse_float=Decimal)
            )
        except (HTTPError, ValueError):
            raise GatewayUnavailable() from None
        return result.data

    async def issue(
        self, account: ConfigWrite, payment: CryptoPaymentModel
    ) -> GatewayInvoice:
        """Create one hosted Plisio invoice for the saved quote.

        Args:
            account: The issuing account settings.
            payment: The stored attempt and its original quote.

        Returns:
            Plisio's invoice identity and customer checkout URL.

        Raises:
            GatewayUnavailable: No valid hosted invoice was returned.
        """
        base = str(account.callback_base_url).rstrip("/")
        callback = (
            f"{base}/hooks/crypto-payments/plisio/{payment.gateway_id}"
            "?json=true"
        )
        params = {
            "source_amount": format(payment.price_amount, "f"),
            "source_currency": payment.price_currency.upper(),
            "order_name": str(payment.id),
            "order_number": str(payment.id),
            "callback_url": callback,
        }
        if payment.pay_currency is not None:
            currency = payment.pay_currency.upper()
            params.update(currency=currency, allowed_psys_cids=currency)
        invoice = await self._get(
            account, "invoices/new", Success[InvoiceOut], **params
        )
        return GatewayInvoice(id=invoice.txn_id, url=str(invoice.invoice_url))

    def verify(
        self, account: ConfigWrite, body: bytes, signature: str | None
    ) -> GatewayNotice:
        """Verify the signature carried in Plisio's JSON callback."""
        if signature is not None:
            raise UnAuthorizedException(
                "Invalid payment notification.", "invalid_crypto_ipn"
            )
        notice = decode_notice(body, account.api_key.get_secret_value())
        return GatewayNotice(
            payment_id=notice.txn_id,
            invoice_id=notice.switch_id or notice.txn_id,
            status=STATES.get(notice.status),
        )

    async def read(
        self, account: ConfigWrite, payment_id: str
    ) -> GatewayPayment:
        """Obtain the operation identity and its settlement facts.

        Args:
            account: The verified issuing account settings.
            payment_id: Operation identity from a verified Plisio notice.

        Returns:
            Independent operation facts for the exact quote and transfer.

        Raises:
            GatewayUnavailable: The operation or required fields are unusable.
        """
        found = await self._get(
            account, f"operations/{payment_id}", Success[OperationOut]
        )
        if found.id != payment_id:
            raise GatewayUnavailable()
        return GatewayPayment(
            id=found.id,
            invoice_id=found.parent_id or found.id,
            order_id=found.params.order_number,
            status=STATES.get(found.status),
            price_amount=found.params.source_amount,
            price_currency=found.params.source_currency,
            pay_amount=found.sum,
            pay_currency=found.psys_cid,
            actually_paid=found.actual_sum,
        )

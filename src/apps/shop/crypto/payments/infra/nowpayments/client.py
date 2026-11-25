"""Issue and inspect NOWPayments invoices using the native HTTP pool."""

from decimal import Decimal
from json import loads

from httpx import HTTPError
from papilio.errors.exceptions import UnAuthorizedException
from papilio.infra.http.connection import HTTPConnection
from papilio.infra.http.gateway import BaseGateway
from pydantic import ValidationError

from src.apps.shop.crypto.gateways.domain.models.records import (
    CryptoGatewayModel,
)

from ...config import CryptoPaymentsConfig
from ...domain.enums.records import CryptoPaymentStatus
from ...domain.errors import GatewayUnavailable
from ...domain.models.records import CryptoPaymentModel
from ...domain.results.gateway import (
    GatewayInvoice,
    GatewayNotice,
    GatewayPayment,
)
from .config import NowPaymentsConfig
from .schemas import InvoiceOut, NoticeIn, PaymentOut
from .signature import verify_signature

STATES = {
    "finished": CryptoPaymentStatus.CONFIRMED,
    "partially_paid": CryptoPaymentStatus.PARTIAL,
}


class NowPaymentsGateway(BaseGateway):
    def __init__(
        self, connection: HTTPConnection, config: CryptoPaymentsConfig
    ) -> None:
        """Use the native HTTP pool and account-specific settings."""
        super().__init__(connection)
        self.config = config

    def _account(self, gateway: CryptoGatewayModel) -> NowPaymentsConfig:
        account = self.config.nowpayments.get(gateway.key)
        if gateway.kind != "nowpayments" or account is None:
            raise GatewayUnavailable(configured=False)
        return account

    def price_decimals(self, gateway: CryptoGatewayModel) -> int:
        """Resolve the configured precision before reserving a payment."""
        return self._account(gateway).price_decimals

    async def issue(
        self, gateway: CryptoGatewayModel, payment: CryptoPaymentModel
    ) -> GatewayInvoice:
        """Create one hosted invoice and validate its echoed quote.

        Args:
            gateway: Configured gateway account selected for this payment.
            payment: Saved attempt with its frozen price.

        Returns:
            The provider invoice ID and HTTPS link.

        Raises:
            GatewayUnavailable: A valid invoice response could not be verified.
        """
        account = self._account(gateway)
        callback_base = str(account.callback_base_url).rstrip("/")
        callback = f"{callback_base}/hooks/crypto-payments/{gateway.id}"
        order_id = str(payment.id)
        data = {
            "price_amount": format(payment.price_amount, "f"),
            "price_currency": payment.price_currency.lower(),
            "order_id": order_id,
            "ipn_callback_url": callback,
        }
        if payment.pay_currency is not None:
            data["pay_currency"] = payment.pay_currency.lower()
        endpoint = str(account.api_url).rstrip("/")
        try:
            response = await self.post(
                f"{endpoint}/invoice",
                headers={"x-api-key": account.api_key.get_secret_value()},
                json=data,
            )
            response.raise_for_status()
            invoice = InvoiceOut.model_validate(
                loads(response.content, parse_float=Decimal)
            )
        except (HTTPError, ValueError):
            raise GatewayUnavailable() from None
        if (
            invoice.order_id != order_id
            or invoice.price_amount != payment.price_amount
            or invoice.price_currency.casefold()
            != payment.price_currency.casefold()
            or (
                payment.pay_currency is not None
                and (invoice.pay_currency or "").casefold()
                != payment.pay_currency.casefold()
            )
        ):
            raise GatewayUnavailable()
        return GatewayInvoice(id=invoice.id, url=str(invoice.invoice_url))

    def verify(
        self, gateway: CryptoGatewayModel, body: bytes, signature: str
    ) -> GatewayNotice:
        """Authenticate a notification before using any of its identifiers."""
        account = self._account(gateway)
        if not verify_signature(
            body, signature, account.ipn_secret.get_secret_value()
        ):
            raise UnAuthorizedException(
                "Invalid payment notification.", "invalid_crypto_ipn"
            )
        try:
            notice = NoticeIn.model_validate_json(body)
        except ValidationError:
            raise UnAuthorizedException(
                "Invalid payment notification.", "invalid_crypto_ipn"
            ) from None
        return GatewayNotice(
            payment_id=notice.payment_id,
            invoice_id=notice.invoice_id,
            status=STATES.get(notice.payment_status),
        )

    async def read(
        self, gateway: CryptoGatewayModel, payment_id: str
    ) -> GatewayPayment:
        """Read payment facts through the authenticated status endpoint.

        Args:
            gateway: Account which issued the invoice.
            payment_id: Numeric provider identity from an authenticated notice.

        Returns:
            Verified observations, independent of the notification payload.

        Raises:
            GatewayUnavailable: The status response was not usable.
        """
        account = self._account(gateway)
        endpoint = str(account.api_url).rstrip("/")
        try:
            response = await self.get(
                f"{endpoint}/payment/{payment_id}",
                headers={"x-api-key": account.api_key.get_secret_value()},
            )
            response.raise_for_status()
            paid = PaymentOut.model_validate(
                loads(response.content, parse_float=Decimal)
            )
        except (HTTPError, ValueError):
            raise GatewayUnavailable() from None
        if paid.payment_id != payment_id:
            raise GatewayUnavailable()
        return GatewayPayment(
            id=paid.payment_id,
            invoice_id=paid.invoice_id,
            order_id=paid.order_id,
            status=STATES.get(paid.payment_status),
            price_amount=paid.price_amount,
            price_currency=paid.price_currency,
            pay_amount=paid.pay_amount,
            pay_currency=paid.pay_currency,
            actually_paid=paid.actually_paid,
        )

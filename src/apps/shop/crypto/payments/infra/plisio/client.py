"""Issue hosted Plisio invoices and obtain authenticated payment facts."""

from decimal import Decimal
from json import loads

from httpx import HTTPError
from papilio.errors.exceptions import UnAuthorizedException
from papilio.infra.http.gateway import BaseGateway
from pydantic import BaseModel

from src.apps.shop.crypto.gateways.domain.dtos.configs import (
    ConfigWrite,
    PlisioConfig,
)

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


def _payment(
    operation: OperationOut, status: CryptoPaymentStatus | None
) -> GatewayPayment:
    """Project the exact quote and transfer facts of an operation."""
    if (
        operation.params is None
        or operation.sum is None
        or operation.psys_cid is None
    ):
        raise GatewayUnavailable()
    return GatewayPayment(
        id=operation.id,
        invoice_id=operation.parent_id or operation.id,
        order_id=operation.params.order_number,
        status=status,
        price_amount=operation.params.source_amount,
        price_currency=operation.params.source_currency,
        pay_amount=operation.sum,
        pay_currency=operation.psys_cid,
        actually_paid=operation.actual_sum,
    )


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
        found = await self._operation(account, payment_id)
        return _payment(found, STATES.get(found.status))

    async def _operation(
        self, account: ConfigWrite, payment_id: str
    ) -> OperationOut:
        found = await self._get(
            account, f"operations/{payment_id}", Success[OperationOut]
        )
        if found.id != payment_id:
            raise GatewayUnavailable()
        return found

    async def read_invoice(
        self, account: PlisioConfig, invoice_id: str
    ) -> GatewayPayment | None:
        """Read the original invoice and up to three currency switches.

        Args:
            account: The original issuing account.
            invoice_id: Saved Plisio invoice identity.

        Returns:
            An actionable observation, or None while no outcome is verified.
        """
        found = await self._operation(account, invoice_id)
        status = STATES.get(found.status)
        observation = _payment(found, status) if status is not None else None
        if found.status == "cancelled" and found.actual_sum == 0:
            if not found.parent_id and not found.child_ids:
                observation = _payment(found, CryptoPaymentStatus.EXPIRED)
        if status is not CryptoPaymentStatus.CONFIRMED:
            for child_id in found.child_ids[:3]:
                child = await self._operation(account, child_id)
                child_status = STATES.get(child.status)
                if child.parent_id == invoice_id and child_status is not None:
                    observation = _payment(child, child_status)
                    if child_status is CryptoPaymentStatus.CONFIRMED:
                        break
        return observation

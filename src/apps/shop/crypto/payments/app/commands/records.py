"""Issue hosted invoices and reconcile authenticated settlement notices."""

from decimal import ROUND_UP, Decimal, localcontext

from papilio.errors.exceptions import ConflictException
from papilio.infra.db.transaction import active_transaction, transaction

from src.apps.shop.crypto.gateways.app.interfaces.services import (
    ICryptoGatewayService,
)

from ...domain.dtos.records import CryptoPaymentCreate, PaymentIssue
from ...domain.enums.records import CryptoPaymentStatus
from ...domain.errors import GatewayUnavailable
from ...domain.models.records import CryptoPaymentModel
from ...domain.results.gateway import GatewayPayment
from ..interfaces.gateway import ICryptoPaymentGateway
from ..interfaces.services import ICryptoPaymentService


def _quote(amount: int, rate: Decimal, places: int) -> Decimal:
    """Calculate the payable quote without a binary-float conversion."""
    with localcontext() as digits:
        digits.prec = 64
        price = (Decimal(amount) / rate).quantize(
            Decimal(1).scaleb(-places), rounding=ROUND_UP
        )
    return price


def _settlement(
    payment: CryptoPaymentModel, observed: GatewayPayment
) -> CryptoPaymentStatus | None:
    """Return the observed outcome for the exact saved invoice."""
    if (
        observed.invoice_id != payment.invoice_id
        or observed.order_id != str(payment.id)
        or observed.price_amount != payment.price_amount
        or observed.price_currency.casefold()
        != payment.price_currency.casefold()
        or (
            payment.pay_currency is not None
            and observed.pay_currency.casefold()
            != payment.pay_currency.casefold()
        )
    ):
        raise ConflictException(
            message="The observed payment does not match the saved invoice.",
            message_code="crypto_invoice_mismatch",
            unique_dict={"id": payment.id},
        )
    status = observed.status
    if status is CryptoPaymentStatus.CONFIRMED:
        if observed.actually_paid is None:
            raise GatewayUnavailable(payment_id=payment.id)
        if observed.actually_paid < observed.pay_amount:
            status = CryptoPaymentStatus.PARTIAL
    return status


class CryptoPaymentCommand:
    def __init__(
        self,
        gateways: ICryptoGatewayService,
        payments: ICryptoPaymentService,
        gateway: ICryptoPaymentGateway,
    ) -> None:
        """Bind request-local payment owners and the shared gateway adapter."""
        self.gateways = gateways
        self.payments = payments
        self.gateway = gateway

    async def issue(self, data: PaymentIssue) -> CryptoPaymentModel:
        """Reserve an attempt, call the provider, then persist its invoice.

        Args:
            data: Gateway identity and authoritative requested amount in rials.

        Returns:
            The saved attempt with its invoice ID and hosted checkout URL.

        Raises:
            GatewayUnavailable: The account is not configured, or issuance is
                unverified. In the latter case the reserved identity survives.
            ConflictException: The selected account does not accept invoices.
        """
        if active_transaction() is not None:
            raise RuntimeError("Crypto issuance requires its own SQL phases")
        async with transaction():
            gateway = await self.gateways.get_by_id(data.gateway_id)
            if (
                not gateway.is_active
                or gateway.price_currency is None
                or gateway.rial_rate is None
            ):
                raise ConflictException(
                    message="This gateway does not accept new payments.",
                    message_code="crypto_gateway_inactive",
                    unique_dict={},
                )
            price = _quote(
                data.amount,
                gateway.rial_rate,
                self.gateway.price_decimals(gateway),
            )
            payment = await self.payments.create(
                CryptoPaymentCreate(
                    gateway_id=gateway.id,
                    amount=data.amount,
                    price_amount=price,
                    price_currency=gateway.price_currency,
                    pay_currency=gateway.pay_currency,
                )
            )
        try:
            invoice = await self.gateway.issue(gateway, payment)
        except GatewayUnavailable:
            raise GatewayUnavailable(payment_id=payment.id) from None
        async with transaction():
            saved = await self.payments.set_invoice(payment.id, invoice)
        return saved

    async def receive(
        self, gateway_id: int, body: bytes, signature: str
    ) -> CryptoPaymentModel | None:
        """Reconcile a signed notice with the gateway and the stored attempt.

        Args:
            gateway_id: Account named in the original invoice callback URL.
            body: Unmodified, size-bounded notice bytes.
            signature: Provider signature header.

        Returns:
            The current record for an actionable notice, otherwise None.
        """
        if active_transaction() is not None:
            raise RuntimeError(
                "Crypto reconciliation requires its own SQL phases"
            )
        payment = None
        async with transaction():
            gateway = await self.gateways.get_by_id(gateway_id)
            notice = self.gateway.verify(gateway, body, signature)
            if notice.status is not None and notice.invoice_id is not None:
                payment = await self.payments.get_by_invoice(
                    gateway_id, notice.invoice_id
                )

        if payment is not None and payment.status in (
            CryptoPaymentStatus.PENDING,
            CryptoPaymentStatus.PARTIAL,
        ):
            observed = await self.gateway.read(gateway, notice.payment_id)
            status = _settlement(payment, observed)
            if status is None:
                raise GatewayUnavailable(payment_id=payment.id)
            async with transaction():
                payment = await self.payments.settle(
                    payment.id, status, observed.id
                )
        return payment

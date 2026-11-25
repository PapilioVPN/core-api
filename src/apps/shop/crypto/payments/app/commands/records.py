"""Issue hosted invoices and reconcile authenticated settlement notices."""

from asyncio import timeout
from collections.abc import Mapping
from datetime import timedelta
from decimal import ROUND_UP, Decimal, localcontext
from logging import getLogger

from papilio.errors.exceptions import (
    ConflictException,
    NotFoundException,
    UnAuthorizedException,
)
from papilio.infra.db.transaction import active_transaction, transaction
from papilio.utils.dates import utc_now

from src.apps.shop.crypto.gateways.app.interfaces.configs import (
    ICryptoGatewayConfigService,
)
from src.apps.shop.crypto.gateways.app.interfaces.services import (
    ICryptoGatewayService,
)
from src.apps.shop.crypto.gateways.domain.dtos.configs import PlisioConfig
from src.apps.shop.crypto.gateways.domain.errors import ConfigUnavailable

from ...domain.dtos.records import CryptoPaymentCreate, PaymentIssue
from ...domain.enums.records import CryptoPaymentStatus
from ...domain.errors import GatewayUnavailable
from ...domain.models.records import CryptoPaymentModel
from ...domain.results.gateway import GatewayPayment
from ..interfaces.gateway import ICryptoInvoiceProbe, ICryptoPaymentGateway
from ..interfaces.services import ICryptoPaymentService

logger = getLogger(__name__)


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
        configs: ICryptoGatewayConfigService,
        payments: ICryptoPaymentService,
        adapters: Mapping[str, ICryptoPaymentGateway],
        invoice_probe: ICryptoInvoiceProbe,
    ) -> None:
        """Bind request-local payment owners and the shared adapters."""
        self.gateways = gateways
        self.configs = configs
        self.payments = payments
        self.adapters = adapters
        self.invoice_probe = invoice_probe

    def _adapter(self, kind: str | None) -> ICryptoPaymentGateway:
        """Resolve supported infrastructure from the saved gateway type."""
        adapter = self.adapters.get(kind) if kind is not None else None
        if adapter is None:
            raise GatewayUnavailable(configured=False)
        return adapter

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
            adapter = self._adapter(gateway.kind)
            account = await self.configs.connection(gateway)
            price = _quote(
                data.amount,
                gateway.rial_rate,
                account.price_decimals,
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
            invoice = await adapter.issue(account, payment)
        except GatewayUnavailable:
            raise GatewayUnavailable(payment_id=payment.id) from None
        async with transaction():
            saved = await self.payments.set_invoice(payment.id, invoice)
        return saved

    async def receive(
        self, gateway_id: int, body: bytes, signature: str | None = None
    ) -> CryptoPaymentModel | None:
        """Reconcile a signed notice with the gateway and the stored attempt.

        Args:
            gateway_id: Account named in the original invoice callback URL.
            body: Unmodified, size-bounded notice bytes.
            signature: Signature header when the provider signs out of band.

        Returns:
            The current record for an actionable notice, otherwise None.
        """
        if active_transaction() is not None:
            raise RuntimeError(
                "Crypto reconciliation requires its own SQL phases"
            )
        payment = None
        async with transaction():
            try:
                gateway = await self.gateways.get_by_id(gateway_id)
            except NotFoundException:
                raise UnAuthorizedException(
                    "Invalid payment notification.", "invalid_crypto_ipn"
                ) from None
            adapter = self._adapter(gateway.kind)
            account = await self.configs.connection(gateway)
            notice = adapter.verify(account, body, signature)
            if notice.status is not None and notice.invoice_id is not None:
                payment = await self.payments.get_by_invoice(
                    gateway_id, notice.invoice_id
                )

        if payment is not None and payment.status in (
            CryptoPaymentStatus.PENDING,
            CryptoPaymentStatus.PARTIAL,
        ):
            observed = await adapter.read(account, notice.payment_id)
            payment = await self._apply(payment, observed)
        return payment

    async def _apply(
        self, payment: CryptoPaymentModel, observed: GatewayPayment
    ) -> CryptoPaymentModel:
        """Validate and store one observation through settlement."""
        status = _settlement(payment, observed)
        if status is None:
            raise GatewayUnavailable(payment_id=payment.id)
        async with transaction():
            saved = await self.payments.settle(payment.id, status, observed.id)
        return saved

    async def recheck(self, *, limit: int, delay: int) -> int:
        """Check one due batch without holding SQL during provider requests.

        Args:
            limit: Maximum payments selected and attempted by this job.
            delay: Minimum seconds since creation or the previous check.

        Returns:
            Due records taken, including recoverable provider failures.
        """
        if active_transaction() is not None:
            raise RuntimeError(
                "Crypto reconciliation requires its own SQL phases"
            )
        now = utc_now()
        accounts: dict[int, PlisioConfig] = {}
        async with transaction():
            batch = await self.payments.take_due(
                kind="plisio",
                now=now,
                before=now - timedelta(seconds=delay),
                limit=limit,
            )
            if batch:
                gateways = await self.gateways.get_by_ids(
                    list({payment.gateway_id for payment in batch})
                )
                for gateway in gateways:
                    try:
                        account = await self.configs.connection(gateway)
                    except ConfigUnavailable:
                        logger.warning("Cannot recheck gateway %s", gateway.id)
                    else:
                        if account.kind == "plisio":
                            accounts[gateway.id] = account

        for payment in batch:
            account = accounts.get(payment.gateway_id)
            if account is None or payment.invoice_id is None:
                continue
            try:
                async with timeout(10):
                    observed = await self.invoice_probe.read_invoice(
                        account, payment.invoice_id
                    )
                if observed is not None:
                    await self._apply(payment, observed)
            except (GatewayUnavailable, ConflictException, TimeoutError):
                logger.warning("Cannot verify crypto payment %s", payment.id)
        return len(batch)

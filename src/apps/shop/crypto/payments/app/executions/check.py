"""Read the original Plisio quote and record a verified settlement."""

from datetime import timedelta

from dishka import AsyncContainer
from papilio.errors.exceptions import ConflictException
from papilio.infra.db.tools.decorators import transactional
from papilio.infra.scopes import Inject, request_scoped
from papilio.utils.dates import utc_now
from papilio_tasks.apps.outbox import OutboxWriter

from src.apps.shop.crypto.gateways.app.interfaces.configs import (
    IPlisioConfigQuery,
)
from src.apps.shop.crypto.gateways.app.interfaces.services import (
    ICryptoGatewayService,
)

from ...domain.events.records import PaymentConfirmed
from ...domain.models.records import CryptoPaymentModel
from ...domain.results.check import PlisioCheck
from ...infra.broker.publishers import payment_confirmed
from ..interfaces.services import ICryptoPaymentService


class PaymentCheckExecution:
    def __init__(self, container: AsyncContainer) -> None:
        """Bind the native container for short payment scopes."""
        self.container = container

    @request_scoped
    @transactional
    async def claim(
        self,
        *,
        limit: int,
        delay: int,
        payments: ICryptoPaymentService = Inject(),
    ) -> tuple[int, ...]:
        """Reserve issued payments for one scheduled check.

        Args:
            limit: Maximum batch size.
            delay: Minimum seconds between attempts for the same payment.
            payments: The injected payment service for this write.

        Returns:
            The committed batch of eligible payment IDs.
        """
        now = utc_now()
        before = now - timedelta(seconds=delay)
        ids = await payments.claim(now=now, before=before, limit=limit)
        return ids

    @request_scoped
    @transactional
    async def prepare(
        self,
        id: int,
        *,
        payments: ICryptoPaymentService = Inject(),
        gateways: ICryptoGatewayService = Inject(),
        configs: IPlisioConfigQuery = Inject(),
    ) -> PlisioCheck | CryptoPaymentModel:
        """Load an issued payment and the account that issued it.

        Args:
            id: Local payment identity.
            payments: Current payment records.
            gateways: Current gateway accounts.
            configs: Internal Plisio credentials reader.

        Returns:
            The settled payment or the inputs for checking it.

        Raises:
            ConflictException: No Plisio invoice can be checked.
        """
        payment = await payments.get_by_id(id)
        result: PlisioCheck | CryptoPaymentModel = payment
        if payment.confirmed_at is None:
            gateway = await gateways.get_by_id(payment.gateway_id)
            if (
                gateway.kind != "plisio"
                or payment.invoice_id is None
                or payment.quote_amount is None
                or payment.quote_currency is None
            ):
                raise ConflictException(
                    message="This payment has no Plisio invoice to check.",
                    message_code="crypto_payment_check_unsupported",
                    unique_dict={"payment_id": id},
                )
            config = await configs.get(gateway.id)
            result = PlisioCheck(payment, payment.invoice_id, config)
        return result

    @request_scoped
    @transactional
    async def complete(
        self,
        id: int,
        invoice_id: str,
        settlement_id: str,
        *,
        payments: ICryptoPaymentService = Inject(),
        outbox: OutboxWriter = Inject(),
    ) -> CryptoPaymentModel:
        """Persist the first verified settlement and register its event.

        Args:
            id: Local payment identity.
            invoice_id: Original provider invoice identity.
            settlement_id: Verified operation that received the payment.
            payments: Payment service injected for the short write.
            outbox: Native writer for the same transaction.

        Returns:
            The stored payment, including after a concurrent confirmation.
        """
        payment = await payments.confirm(
            id, invoice_id, settlement_id, utc_now()
        )
        if payment is not None:
            await outbox.append(
                payment_confirmed, PaymentConfirmed(payment_id=payment.id)
            )
        else:
            payment = await payments.get_by_id(id)
        return payment

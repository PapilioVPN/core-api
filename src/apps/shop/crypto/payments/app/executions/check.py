"""Read the original Plisio quote and record a verified settlement."""

from datetime import timedelta

from dishka import AsyncContainer
from papilio.infra.db.tools.decorators import transactional
from papilio.infra.scopes import Inject, request_scoped
from papilio.utils.dates import utc_now

from src.apps.shop.crypto.gateways.app.interfaces.configs import (
    IPlisioConfigQuery,
)
from src.apps.shop.crypto.gateways.app.interfaces.services import (
    ICryptoGatewayService,
)
from src.apps.shop.crypto.gateways.domain.results.configs import ConfigFailure

from ...domain.models.records import CryptoPaymentModel
from ...domain.policy import PLISIO
from ...domain.results.check import PlisioCheck
from ...domain.results.records import PaymentFailure
from ...domain.results.settlement import Settlement
from ..interfaces.commands import IPaymentConfirmCommand
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
    ) -> PlisioCheck | CryptoPaymentModel | ConfigFailure | PaymentFailure:
        """Load an issued payment and the account that issued it.

        Args:
            id: Local payment identity.
            payments: Current payment records.
            gateways: Current gateway accounts.
            configs: Internal Plisio credentials reader.

        Returns:
            The settled payment, check inputs, or the unavailability reason.
        """
        payment = await payments.get_by_id(id)
        result: (
            PlisioCheck | CryptoPaymentModel | ConfigFailure | PaymentFailure
        ) = payment
        if payment.confirmed_at is None:
            gateway = await gateways.get_by_id(payment.gateway_id)
            if (
                gateway.kind != PLISIO
                or payment.invoice_id is None
                or payment.quote_amount is None
                or payment.quote_currency is None
            ):
                result = PaymentFailure.CHECK_UNAVAILABLE
            else:
                config = await configs.get(gateway.id)
                result = (
                    config
                    if isinstance(config, ConfigFailure)
                    else PlisioCheck(payment, payment.invoice_id, config)
                )
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
        command: IPaymentConfirmCommand = Inject(),
    ) -> CryptoPaymentModel:
        """Persist the first verified settlement and register its event.

        Args:
            id: Local payment identity.
            invoice_id: Original provider invoice identity.
            settlement_id: Verified operation that received the payment.
            payments: Payment service injected for the short write.
            command: Shared command that commits confirmation and publication.

        Returns:
            The stored payment, including after a concurrent confirmation.
        """
        payment = await command.confirm(
            Settlement(id, invoice_id, settlement_id)
        )
        if payment is None:
            payment = await payments.get_by_id(id)
        return payment

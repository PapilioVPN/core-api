"""Resolve a signed notification to a verified local settlement."""

from papilio.infra.db.tools.decorators import transactional
from pydantic import JsonValue

from src.apps.shop.crypto.gateways.app.interfaces.configs import (
    INowPaymentsConfigQuery,
)
from src.apps.shop.crypto.gateways.domain.results.configs import ConfigFailure

from ...domain.policy import matches_invoice
from ...domain.results.records import PaymentFailure
from ...domain.results.settlement import Settlement
from ..interfaces.gateways import INowPaymentsNotification
from ..interfaces.services import ICryptoPaymentService


class PaymentNotificationService:
    def __init__(
        self,
        configs: INowPaymentsConfigQuery,
        decoder: INowPaymentsNotification,
        payments: ICryptoPaymentService,
    ) -> None:
        """Bind account credentials, the wire decoder and payment records."""
        self.configs = configs
        self.decoder = decoder
        self.payments = payments

    @transactional
    async def verify(
        self, gateway_id: int, data: dict[str, JsonValue], signature: str
    ) -> Settlement | ConfigFailure | PaymentFailure | None:
        """Match a final signed notification to its original local invoice.

        Args:
            gateway_id: Account receiving the notification.
            data: The unchanged provider body.
            signature: The provider's HMAC header value.

        Returns:
            Verified evidence, None for nonfinal status, or a failure.
        """
        config = await self.configs.find(gateway_id)
        if config is None:
            result: Settlement | ConfigFailure | PaymentFailure | None = (
                PaymentFailure.INVALID_NOTIFICATION
            )
        elif isinstance(config, ConfigFailure):
            result = config
        else:
            invoice = self.decoder.decode(
                data, signature, config.ipn_secret.get_secret_value()
            )
            if invoice is None or isinstance(invoice, PaymentFailure):
                result = invoice
            else:
                payment = await self.payments.get_by_id(
                    invoice.settlement.payment_id
                )
                result = (
                    invoice.settlement
                    if matches_invoice(gateway_id, payment, invoice)
                    else PaymentFailure.INVOICE_MISMATCH
                )
        return result

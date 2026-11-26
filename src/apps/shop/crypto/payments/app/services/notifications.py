"""Resolve a signed notification to a verified local settlement."""

from papilio.infra.db.tools.decorators import transactional
from pydantic import JsonValue

from src.apps.shop.crypto.gateways.app.interfaces.configs import (
    INowPaymentsConfigQuery,
)

from ...domain.errors import InvalidNotification
from ...domain.policy import check_invoice
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
    ) -> Settlement | None:
        """Match a final signed notification to its original local invoice.

        Args:
            gateway_id: Account receiving the notification.
            data: The unchanged provider body.
            signature: The provider's HMAC header value.

        Returns:
            The settlement when verified, or None for nonfinal updates.

        Raises:
            UnAuthorizedException: The account or signature is invalid.
            ConflictException: The evidence does not match a paid invoice.
        """
        config = await self.configs.find(gateway_id)
        if config is None:
            raise InvalidNotification()
        invoice = self.decoder.decode(
            gateway_id, data, signature, config.ipn_secret.get_secret_value()
        )
        settlement = None
        if invoice is not None:
            payment = await self.payments.get_by_id(
                invoice.settlement.payment_id
            )
            check_invoice(gateway_id, payment, invoice)
            settlement = invoice.settlement
        return settlement

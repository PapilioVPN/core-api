"""Register a local payment with an active gateway."""

from papilio.infra.db.tools.decorators import transactional

from src.apps.shop.crypto.gateways.app.interfaces.services import (
    ICryptoGatewayService,
)

from ...domain.dtos.records import PaymentCreate
from ...domain.models.records import CryptoPaymentModel
from ...domain.policy import check_amount
from ..interfaces.services import ICryptoPaymentService


class PaymentCreateCommand:
    def __init__(
        self, gateways: ICryptoGatewayService, payments: ICryptoPaymentService
    ) -> None:
        """Bind the gateway reader and payment record service."""
        self.gateways = gateways
        self.payments = payments

    @transactional
    async def create(self, data: PaymentCreate) -> CryptoPaymentModel:
        """Register a payment before any external request.

        Args:
            data: Selected gateway ID and original positive amount in rials.

        Returns:
            The stored payment with its internal identity.

        Raises:
            NotFoundException: The gateway does not exist.
            ValidationException: The gateway does not accept new payments.
        """
        gateway = await self.gateways.get_by_id(data.gateway_id)
        check_amount(gateway, data.amount)
        payment = await self.payments.create(
            CryptoPaymentModel(gateway_id=gateway.id, amount=data.amount)
        )
        return payment

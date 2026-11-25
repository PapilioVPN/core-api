"""Create local payment records before contacting a provider."""

from papilio.errors.exceptions import ConflictException
from papilio.infra.db.tools.decorators import transactional

from src.apps.shop.crypto.gateways.app.interfaces.services import (
    ICryptoGatewayService,
)

from ...domain.dtos.records import PaymentCreate
from ...domain.models.records import CryptoPaymentModel
from ...infra.pg.repositories.crud import CryptoPaymentRepository


class CryptoPaymentService:
    def __init__(
        self, repo: CryptoPaymentRepository, gateways: ICryptoGatewayService
    ) -> None:
        """Bind the request repository and gateway account lookup."""
        self.repo = repo
        self.gateways = gateways

    @transactional
    async def create(self, data: PaymentCreate) -> CryptoPaymentModel:
        """Record a payment before any external request.

        Args:
            data: Selected gateway ID and original positive amount in rials.

        Returns:
            The stored payment with its internal identity.

        Raises:
            NotFoundException: The gateway does not exist.
            ConflictException: The gateway does not accept new payments.
        """
        gateway = await self.gateways.get_by_id(data.gateway_id)
        if not gateway.is_active:
            raise ConflictException(
                message="This gateway does not accept new payments.",
                message_code="crypto_gateway_inactive",
                unique_dict={"gateway_id": gateway.id},
            )
        payment = await self.repo.create(
            CryptoPaymentModel(gateway_id=gateway.id, amount=data.amount)
        )
        return payment

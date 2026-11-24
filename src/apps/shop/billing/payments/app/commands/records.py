"""Create a payment and its receipt in one native transaction."""

from papilio.infra.db.tools.decorators import transactional

from src.apps.shop.billing.receipts.app.interfaces.services import (
    IReceiptService,
)
from src.apps.shop.billing.receipts.domain.models.records import ReceiptModel

from ...domain.dtos.records import PaymentCreate
from ...domain.models.records import PaymentModel
from ..interfaces.services import IPaymentService


class PaymentCommand:
    def __init__(
        self, payments: IPaymentService, receipts: IReceiptService
    ) -> None:
        """Bind the owning record services on the request UoW."""
        self.payments = payments
        self.receipts = receipts

    @transactional
    async def create(self, data: PaymentCreate) -> PaymentModel:
        """Register a pending payment and its raw receipt.

        Args:
            data: Expected payment amount in rials and uploaded image address.

        Returns:
            Stored payment with the identity of its pending receipt.
        """
        receipt = await self.receipts.create(
            ReceiptModel(image_url=data.image_url)
        )
        payment = await self.payments.create(
            PaymentModel(receipt_id=receipt.id, amount=data.amount)
        )
        return payment

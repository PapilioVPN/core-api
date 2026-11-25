"""Create a payment and its receipt in one native transaction."""

from papilio.errors.exceptions import ValidationException
from papilio.infra.db.tools.decorators import transactional

from src.apps.shop.billing.payment_settings.app.interfaces.services import (
    IPaymentSettingsService,
)
from src.apps.shop.billing.receipts.app.interfaces.services import (
    IReceiptService,
)
from src.apps.shop.billing.receipts.domain.models.records import ReceiptModel

from ...domain.dtos.records import PaymentCreate
from ...domain.models.records import PaymentModel
from ..interfaces.services import IPaymentService


class PaymentCommand:
    def __init__(
        self,
        payments: IPaymentService,
        receipts: IReceiptService,
        settings: IPaymentSettingsService,
    ) -> None:
        """Bind the owning record services on the request UoW."""
        self.payments = payments
        self.receipts = receipts
        self.settings = settings

    @transactional
    async def create(self, data: PaymentCreate) -> PaymentModel:
        """Register a pending manual or automatic payment.

        Args:
            data: Original rial amount and an optional uploaded receipt.

        Returns:
            The payment and, in automatic mode, its transfer instructions.

        Raises:
            ValidationException: A manual payment has no receipt.
        """
        settings = await self.settings.get()
        if not settings.auto_confirm and data.image_url is None:
            raise ValidationException(
                message="An image is required for a manual payment",
                message_code="receipt_required",
                loc=["image_url"],
            )
        receipt_id = None
        if data.image_url is not None:
            receipt = await self.receipts.create(
                ReceiptModel(image_url=data.image_url)
            )
            receipt_id = receipt.id

        record = PaymentModel(receipt_id=receipt_id, amount=data.amount)
        if settings.auto_confirm:
            payment = await self.payments.create_auto(record, settings.digits)
        else:
            payment = await self.payments.create(record)
        return payment

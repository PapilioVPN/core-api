"""Register bank payments and reserve exact automatic transfer amounts."""

from papilio.errors.exceptions import ConflictException, ValidationException
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
            ConflictException: No unique transfer amount is available.
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

        if settings.auto_confirm:
            payment = await self.reserve_auto(
                data.amount, settings.digits, receipt_id=receipt_id
            )
        else:
            payment = await self.payments.create(
                PaymentModel(receipt_id=receipt_id, amount=data.amount)
            )
        return payment

    @transactional
    async def reserve_auto(
        self, amount: int, digits: int, *, receipt_id: int | None = None
    ) -> PaymentModel:
        """Reserve a pending payment with a unique transfer amount.

        Args:
            amount: Original amount in whole rials.
            digits: Configured confirmation suffix length.
            receipt_id: Optional receipt already stored in the current scope.

        Returns:
            The pending payment with its exact transfer amount and code.

        Raises:
            ConflictException: No unique transfer amount is available.
        """
        record = PaymentModel(receipt_id=receipt_id, amount=amount)
        payment = None
        for _ in range(3):
            payment = await self.payments.create_auto(record, digits)
            if payment is not None:
                break
        if payment is None:
            raise ConflictException(
                message="No transfer amount is available for this payment",
                message_code="transfer_amount_unavailable",
                unique_dict={"amount": amount},
            )
        return payment

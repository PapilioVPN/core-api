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
from ...domain.enums.records import PaymentStatus
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
        if settings.auto_confirm:
            receipt_id = None
            if data.image_url is not None:
                receipt = await self.receipts.create(
                    ReceiptModel(image_url=data.image_url)
                )
                receipt_id = receipt.id
            payment = await self.reserve_auto(
                data.amount, settings.digits, receipt_id=receipt_id
            )
        else:
            if data.image_url is None:
                raise ValidationException(
                    message="An image is required for a manual payment",
                    message_code="receipt_required",
                    loc=["image_url"],
                )
            payment = await self.create_manual(data.amount, data.image_url)
        return payment

    @transactional
    async def create_manual(self, amount: int, image_url: str) -> PaymentModel:
        """Register a manual payment against its uploaded evidence.

        Args:
            amount: Original amount in whole rials.
            image_url: Uploaded receipt address.

        Returns:
            The pending manual payment and its receipt identity.
        """
        receipt = await self.receipts.create(ReceiptModel(image_url=image_url))
        payment = await self.payments.create(
            PaymentModel(receipt_id=receipt.id, amount=amount)
        )
        return payment

    @transactional
    async def attach_receipt(self, id: int, image_url: str) -> PaymentModel:
        """Record the first receipt on a payment that still awaits review.

        Args:
            id: Stored Billing payment identity.
            image_url: Uploaded receipt address.

        Returns:
            The payment with its current status and receipt identity.

        Raises:
            NotFoundException: The payment does not exist.
            ConflictException: A concurrent submission or decision won.
        """
        payment = await self.payments.get_by_id(id)
        if (
            payment.status == PaymentStatus.PENDING
            and payment.receipt_id is None
        ):
            receipt = await self.receipts.create(
                ReceiptModel(image_url=image_url)
            )
            saved = await self.payments.attach_receipt(id, receipt.id)
            if saved is None:
                raise ConflictException(
                    message="The payment has changed.",
                    message_code="payment_receipt_unavailable",
                    unique_dict={"id": id},
                )
            payment = saved
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

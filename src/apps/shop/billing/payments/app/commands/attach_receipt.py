"""Attach an uploaded receipt to an existing bank payment."""

from papilio.errors.exceptions import ConflictException
from papilio.infra.db.tools.decorators import transactional

from src.apps.shop.billing.receipts.app.interfaces.services import (
    IReceiptService,
)
from src.apps.shop.billing.receipts.domain.models.records import ReceiptModel

from ...domain.enums.records import PaymentStatus
from ...domain.models.records import PaymentModel
from ..interfaces.services import IPaymentService


class PaymentAttachReceiptCommand:
    def __init__(
        self, payments: IPaymentService, receipts: IReceiptService
    ) -> None:
        """Bind payment and receipt records to the request."""
        self.payments = payments
        self.receipts = receipts

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
            ConflictException: The payment cannot accept the supplied receipt.
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
        else:
            receipt = (
                await self.receipts.get_by_id(payment.receipt_id)
                if payment.receipt_id is not None
                else None
            )
            if receipt is None or receipt.image_url != image_url:
                raise ConflictException(
                    message="The payment cannot accept this receipt.",
                    message_code="payment_receipt_unavailable",
                    unique_dict={"id": id},
                )
        return payment

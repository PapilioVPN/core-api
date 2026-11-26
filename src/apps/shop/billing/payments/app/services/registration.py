"""Register bank payments and reserve exact automatic transfer amounts."""

from papilio.errors.exceptions import ConflictException
from papilio.infra.db.tools.decorators import transactional

from src.apps.shop.billing.receipts.app.interfaces.services import (
    IReceiptService,
)
from src.apps.shop.billing.receipts.domain.models.records import ReceiptModel

from ...domain.models.records import PaymentModel
from ..interfaces.services import IPaymentService

RESERVATION_ATTEMPTS = 3


class PaymentRegistrationService:
    def __init__(
        self, payments: IPaymentService, receipts: IReceiptService
    ) -> None:
        """Bind the owners of payment registration and receipt storage."""
        self.payments = payments
        self.receipts = receipts

    async def create_receipt(self, image_url: str) -> ReceiptModel:
        """Create the uploaded receipt inside the caller's transaction.

        Args:
            image_url: Address of an uploaded receipt.

        Returns:
            The receipt with its generated identity.
        """
        receipt = await self.receipts.create(ReceiptModel(image_url=image_url))
        return receipt

    @transactional
    async def create_manual(self, amount: int, image_url: str) -> PaymentModel:
        """Register a manual payment against its uploaded evidence.

        Args:
            amount: Original amount in whole rials.
            image_url: Uploaded receipt address.

        Returns:
            The pending manual payment and its receipt identity.
        """
        receipt = await self.create_receipt(image_url)
        payment = await self.payments.create(
            PaymentModel(receipt_id=receipt.id, amount=amount)
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
        for _ in range(RESERVATION_ATTEMPTS):
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

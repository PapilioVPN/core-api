"""Register bank payments and reserve exact automatic transfer amounts."""

from papilio.errors.exceptions import ConflictException, ValidationException
from papilio.infra.db.tools.decorators import transactional
from papilio.types.constants import INT64_MAX

from src.apps.shop.billing.payment_settings.app.interfaces.services import (
    IPaymentSettingsService,
)
from src.apps.shop.billing.receipts.app.interfaces.services import (
    IReceiptService,
)
from src.apps.shop.billing.receipts.domain.models.records import ReceiptModel

from ...domain.models.records import PaymentModel
from ..interfaces.services import IPaymentService

RESERVATION_ATTEMPTS = 3


class PaymentRegistrationService:
    def __init__(
        self,
        payments: IPaymentService,
        receipts: IReceiptService,
        settings: IPaymentSettingsService,
    ) -> None:
        """Bind the owners of payment registration and receipt storage."""
        self.payments = payments
        self.receipts = receipts
        self.settings = settings

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
    async def reserve_auto(self, amount: int) -> PaymentModel:
        """Reserve a pending payment with a unique transfer amount.

        Args:
            amount: Original amount in whole rials.

        Returns:
            The pending payment with its exact transfer amount and code.

        Raises:
            ValidationException: The amount is invalid.
            ConflictException: Automatic mode is off or no amount is available.
        """
        if type(amount) is not int or not 0 < amount <= INT64_MAX:
            raise ValidationException(
                message="The amount must be a positive rial amount.",
                message_code="payment_amount_invalid",
                loc=["amount"],
            )
        settings = await self.settings.get()
        if not settings.auto_confirm:
            raise ConflictException(
                message="Automatic payment confirmation is disabled.",
                message_code="automatic_payment_disabled",
                unique_dict={},
            )
        record = PaymentModel(amount=amount)
        payment = None
        for _ in range(RESERVATION_ATTEMPTS):
            payment = await self.payments.create_auto(record, settings.digits)
            if payment is not None:
                break
        if payment is None:
            raise ConflictException(
                message="No transfer amount is available for this payment",
                message_code="transfer_amount_unavailable",
                unique_dict={"amount": amount},
            )
        return payment

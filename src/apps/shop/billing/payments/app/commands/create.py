"""Register bank payments and reserve exact automatic transfer amounts."""

from papilio.errors.exceptions import ValidationException
from papilio.infra.db.tools.decorators import transactional

from src.apps.shop.billing.payment_settings.app.interfaces.services import (
    IPaymentSettingsService,
)

from ...domain.dtos.records import PaymentCreate
from ...domain.models.records import PaymentModel
from ..interfaces.services import IPaymentRegistrationService


class PaymentCreateCommand:
    def __init__(
        self,
        settings: IPaymentSettingsService,
        registration: IPaymentRegistrationService,
    ) -> None:
        """Bind payment policy and registration to the request."""
        self.settings = settings
        self.registration = registration

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
                receipt = await self.registration.create_receipt(
                    data.image_url
                )
                receipt_id = receipt.id
            payment = await self.registration.reserve_auto(
                data.amount, settings.digits, receipt_id=receipt_id
            )
        else:
            if data.image_url is None:
                raise ValidationException(
                    message="An image is required for a manual payment",
                    message_code="receipt_required",
                    loc=["image_url"],
                )
            payment = await self.registration.create_manual(
                data.amount, data.image_url
            )
        return payment

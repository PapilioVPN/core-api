"""Register a manual bank payment from its uploaded receipt."""

from ...domain.dtos.records import PaymentCreate
from ...domain.models.records import PaymentModel
from ..interfaces.services import IPaymentRegistrationService


class PaymentCreateCommand:
    def __init__(self, registration: IPaymentRegistrationService) -> None:
        self.registration = registration

    async def create(self, data: PaymentCreate) -> PaymentModel:
        """Register a manual payment from the panel.

        Args:
            data: Amount in whole rials and the uploaded receipt address.

        Returns:
            The pending payment and its receipt identity.
        """
        payment = await self.registration.create_manual(
            data.amount, data.image_url
        )
        return payment

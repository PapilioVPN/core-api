"""Register a pending payment after resolving its customer."""

from papilio.infra.db.tools.decorators import transactional

from src.apps.shop.customers.profiles.app.interfaces.services import (
    ICustomerService,
)

from ...domain.dtos.records import PaymentCreate
from ...domain.models.records import PaymentModel
from ..interfaces.services import IPaymentService


class PaymentCommand:
    def __init__(
        self, payments: IPaymentService, profiles: ICustomerService
    ) -> None:
        """Bind registration to the payment and customer owners.

        Args:
            payments: Owning payment record service.
            profiles: Authoritative customer profile service.

        Returns:
            None.
        """
        self.payments = payments
        self.profiles = profiles

    @transactional
    async def create(self, data: PaymentCreate) -> PaymentModel:
        """Register the pending payment for a trusted source record.

        Args:
            data: Customer, positive rial amount and source reference.
                The calling business flow resolves and authorizes its source.

        Returns:
            The new pending payment and its identity.

        Raises:
            NotFoundException: The customer is absent.
        """
        await self.profiles.get_by_id(data.customer_id)
        payment = await self.payments.create(
            PaymentModel(
                customer_id=data.customer_id,
                source=data.source,
                source_id=data.source_id,
                amount=data.amount,
            )
        )
        return payment

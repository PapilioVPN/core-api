"""Commit the delivery, payment transition and its event together."""

from papilio.infra.db.tools.decorators import transactional
from papilio_tasks.apps.outbox import OutboxWriter

from ...domain.dtos.paid import PaidDelivery
from ...domain.events.records import PaymentConfirmed
from ...domain.models.records import PaymentModel
from ...infra.broker.publishers import payment_confirmed
from ..interfaces.services import IDeliveryService, IPaymentService


class ConfirmPaymentCommand:
    def __init__(
        self,
        deliveries: IDeliveryService,
        payments: IPaymentService,
        outbox: OutboxWriter,
    ) -> None:
        self.deliveries = deliveries
        self.payments = payments
        self.outbox = outbox

    @transactional
    async def confirm(self, delivery: PaidDelivery) -> PaymentModel | None:
        """Store a verified delivery and confirm the payment once.

        Args:
            delivery: Authenticated notification with rial amounts.

        Returns:
            The newly confirmed payment, or None for replay or no match.
        """
        recorded = await self.deliveries.record(delivery)
        payment = None
        if recorded is not None:
            payment = await self.payments.confirm(
                delivery.gateway_id, delivery.transfer
            )
            if payment is not None:
                await self.outbox.append(
                    payment_confirmed, PaymentConfirmed(payment_id=payment.id)
                )
        return payment

"""Record a manual payment decision and its event."""

from papilio.infra.db.tools.decorators import transactional
from papilio_tasks.apps.outbox import OutboxWriter
from papilio_tasks.apps.outbox import decorators as outbox

from ...domain.enums.records import PaymentStatus
from ...domain.events.records import PaymentEvent
from ...domain.models.records import PaymentModel
from ...infra.broker.publishers import payment_confirmed, payment_rejected
from ..interfaces.services import IPaymentService


class PaymentReviewCommand:
    def __init__(
        self, payments: IPaymentService, outbox: OutboxWriter
    ) -> None:
        """Bind payment writes and the native writer to the request."""
        self.payments = payments
        self.outbox = outbox

    @transactional
    @outbox.publish(payment_confirmed, select=PaymentEvent.from_record)
    async def confirm(self, id: int) -> PaymentModel:
        """Confirm a pending payment and register its event."""
        payment = await self.payments.review(id, PaymentStatus.CONFIRMED)
        return payment

    @transactional
    @outbox.publish(payment_rejected, select=PaymentEvent.from_record)
    async def reject(
        self, id: int, *, reason: str | None = None
    ) -> PaymentModel:
        """Reject a pending payment and register its event."""
        payment = await self.payments.review(
            id, PaymentStatus.REJECTED, reason=reason
        )
        return payment

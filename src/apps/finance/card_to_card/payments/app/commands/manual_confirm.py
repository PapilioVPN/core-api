"""Publish the outcome of an operator's payment review."""

from papilio.infra.db.tools.decorators import transactional
from papilio_tasks.apps.outbox import OutboxWriter

from ...domain.dtos.review import CardPaymentReview
from ...domain.enums.records import PaymentStatus
from ...domain.events.records import PaymentConfirmed, PaymentRejected
from ...domain.models.records import CardPaymentModel
from ...infra.broker.publishers import payment_confirmed, payment_rejected
from ..interfaces.services import ICardPaymentService


class ReviewPaymentCommand:
    def __init__(
        self, payments: ICardPaymentService, outbox: OutboxWriter
    ) -> None:
        self.payments = payments
        self.outbox = outbox

    @transactional
    async def review(
        self, id: int, data: CardPaymentReview
    ) -> CardPaymentModel:
        """Commit the operator decision with its corresponding event.

        Args:
            id: Stored payment identity.
            data: Validated decision and optional rejection reason.

        Returns:
            The payment with its recorded decision.

        Raises:
            NotFoundException: The payment does not exist.
            ConflictException: The payment was already decided.
            ValidationException: A confirmation includes a rejection reason.
        """
        payment = await self.payments.review(id, data)
        if payment.status is PaymentStatus.CONFIRMED:
            await self.outbox.append(
                payment_confirmed, PaymentConfirmed(payment_id=payment.id)
            )
        else:
            await self.outbox.append(
                payment_rejected, PaymentRejected(payment_id=payment.id)
            )
        return payment

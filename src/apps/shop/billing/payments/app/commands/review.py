"""Record payment decisions and publish their events."""

from datetime import datetime

from papilio.infra.db.tools.decorators import transactional
from papilio.utils.dates import utc_now
from papilio_tasks.apps.outbox import OutboxWriter
from papilio_tasks.apps.outbox import decorators as outbox

from ...domain.enums.records import PaymentStatus
from ...domain.events.records import PaymentEvent
from ...domain.models.records import PaymentModel
from ...infra.broker.publishers import payment_confirmed, payment_rejected
from ..interfaces.services import IPaymentService


class PaymentConfirmCommand:
    def __init__(
        self, payments: IPaymentService, outbox: OutboxWriter
    ) -> None:
        """Bind payment records and the native outbox to this request."""
        self.payments = payments
        self.outbox = outbox

    @transactional
    @outbox.publish(payment_confirmed, select=PaymentEvent.from_record)
    async def confirm(self, id: int) -> PaymentModel:
        """Confirm a pending payment and register its event."""
        payment = await self.payments.review(
            id, PaymentStatus.CONFIRMED, confirmed_at=utc_now()
        )
        return payment


class PaymentAutoConfirmCommand:
    def __init__(
        self, payments: IPaymentService, outbox: OutboxWriter
    ) -> None:
        """Bind payment writes and the native writer to the request."""
        self.payments = payments
        self.outbox = outbox

    @transactional
    async def confirm_auto(
        self, amount: int, *, since: datetime, until: datetime
    ) -> PaymentModel | None:
        """Record a confirmed payment event only when a deposit matched."""
        payment = await self.payments.confirm_auto(
            amount, since=since, until=until
        )
        if payment is not None:
            await self.outbox.append(
                payment_confirmed, PaymentEvent.from_record(payment)
            )
        return payment


class PaymentRejectCommand:
    def __init__(
        self, payments: IPaymentService, outbox: OutboxWriter
    ) -> None:
        """Bind payment records and the native outbox to this request."""
        self.payments = payments
        self.outbox = outbox

    @transactional
    @outbox.publish(payment_rejected, select=PaymentEvent.from_record)
    async def reject(
        self, id: int, *, reason: str | None = None
    ) -> PaymentModel:
        """Reject a pending payment and register its event."""
        payment = await self.payments.review(
            id, PaymentStatus.REJECTED, confirmed_at=None, reason=reason
        )
        return payment

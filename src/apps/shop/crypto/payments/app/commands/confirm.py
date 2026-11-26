"""Record a verified settlement and its durable confirmation event."""

from papilio.infra.db.tools.decorators import transactional
from papilio.utils.dates import utc_now
from papilio_tasks.apps.outbox import OutboxWriter

from ...domain.events.records import PaymentConfirmed
from ...domain.models.records import CryptoPaymentModel
from ...domain.results.settlement import Settlement
from ...infra.broker.publishers import payment_confirmed
from ..interfaces.services import ICryptoPaymentService


class PaymentConfirmCommand:
    def __init__(
        self, payments: ICryptoPaymentService, outbox: OutboxWriter
    ) -> None:
        """Bind settlement writes and publication to the same transaction."""
        self.payments = payments
        self.outbox = outbox

    @transactional
    async def confirm(self, data: Settlement) -> CryptoPaymentModel | None:
        """Confirm the original invoice and publish once.

        Args:
            data: Verified local payment, invoice and provider references.

        Returns:
            The newly confirmed payment, or None if no update applied.
        """
        payment = await self.payments.confirm(
            data.payment_id, data.invoice_id, data.reference, utc_now()
        )
        if payment is not None:
            await self.outbox.append(
                payment_confirmed, PaymentConfirmed(payment_id=payment.id)
            )
        return payment

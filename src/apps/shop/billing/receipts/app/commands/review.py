"""Apply a receipt review and register its event atomically."""

from papilio.infra.db.tools.decorators import transactional
from papilio.utils.dates import utc_now
from papilio_tasks.apps.outbox import OutboxWriter

from src.apps.shop.billing.payments.app.interfaces.services import (
    IPaymentService,
)
from src.apps.shop.billing.payments.domain.enums.records import PaymentStatus

from ...domain.dtos.review import ReceiptReview
from ...domain.enums.records import ReceiptStatus
from ...domain.events.review import ReceiptApproved, ReceiptRejected
from ...domain.models.records import ReceiptModel
from ...infra.broker.publishers import receipt_approved, receipt_rejected
from ..interfaces.services import IReceiptService


class ReceiptReviewCommand:
    def __init__(
        self,
        receipts: IReceiptService,
        payments: IPaymentService,
        outbox: OutboxWriter,
    ) -> None:
        """Bind the record owners and writer on one request transaction."""
        self.receipts = receipts
        self.payments = payments
        self.outbox = outbox

    @transactional
    async def review(
        self, id: int, data: ReceiptReview, *, actor_id: int
    ) -> ReceiptModel:
        """Record an operator's manual decision without interpreting the image.

        Args:
            id: Stored receipt identity.
            data: Terminal decision and optional rejection reason.
            actor_id: Identity of the verified operator.

        Returns:
            The reviewed receipt.

        Raises:
            NotFoundException: The receipt does not exist.
            ConflictException: Receipt or linked payment is no longer pending.
        """
        receipt = await self.receipts.review(id, data)
        if receipt.status == ReceiptStatus.APPROVED:
            payment = await self.payments.review(
                id, PaymentStatus.CONFIRMED, confirmed_at=utc_now()
            )
            await self.outbox.append(
                receipt_approved,
                ReceiptApproved(
                    receipt_id=id, payment_id=payment.id, actor_id=actor_id
                ),
            )
        else:
            payment = await self.payments.review(
                id, PaymentStatus.REJECTED, confirmed_at=None
            )
            await self.outbox.append(
                receipt_rejected,
                ReceiptRejected(
                    receipt_id=id,
                    payment_id=payment.id,
                    actor_id=actor_id,
                    reason=receipt.rejection_reason,
                ),
            )
        return receipt

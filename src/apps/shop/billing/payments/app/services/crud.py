"""Persist prepared payment records."""

from datetime import datetime

from papilio.errors.exceptions import ConflictException
from papilio.infra.db.tools.decorators import transactional

from ...domain.enums.records import PaymentStatus
from ...domain.models.records import PaymentModel
from ...infra.pg.repositories.crud import PaymentRepository


class PaymentService:
    def __init__(self, repo: PaymentRepository) -> None:
        """Bind the request's payment repository."""
        self.repo = repo

    @transactional
    async def create(self, data: PaymentModel) -> PaymentModel:
        """Register one payment against its receipt.

        Args:
            data: Prepared payment with its receipt ID and amount in rials.

        Returns:
            Stored payment with its identity and timestamps.
        """
        payment = await self.repo.create(data)
        return payment

    @transactional
    async def review(
        self,
        receipt_id: int,
        status: PaymentStatus,
        *,
        confirmed_at: datetime | None,
    ) -> PaymentModel:
        """Record a terminal decision for the receipt's pending payment."""
        payment = await self.repo.review(
            receipt_id, status, confirmed_at=confirmed_at
        )
        if payment is None:
            raise ConflictException(
                message="The receipt has no pending payment",
                message_code="pending_payment_required",
                unique_dict={"receipt_id": receipt_id},
            )
        return payment

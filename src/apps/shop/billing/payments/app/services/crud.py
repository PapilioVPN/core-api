"""Persist prepared payment records."""

from papilio.infra.db.tools.decorators import transactional

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

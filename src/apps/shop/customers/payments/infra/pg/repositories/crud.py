"""Native payment persistence and conditional review writes."""

from papilio.errors.exceptions import ConflictException
from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from sqlalchemy import func, update
from sqlalchemy.exc import IntegrityError
from sqlmodel import col

from ....domain.enums.records import PaymentStatus
from ....domain.models.records import PaymentModel
from ..tables import PaymentTable


class PaymentRepository(PGPersistenceRepository[PaymentModel]):
    table = PaymentTable

    async def create(self, data: PaymentModel) -> PaymentModel:
        """Insert a prepared payment with its destination snapshot.

        Args:
            data: Pending payment with previously resolved references.

        Returns:
            The stored payment.

        Raises:
            ConflictException: A referenced record was removed during creation.
        """
        try:
            payment = await super().create(data)
        except IntegrityError as error:
            if getattr(error.orig, "sqlstate", None) != "23503":
                raise
            raise ConflictException(
                message="A payment reference is no longer available.",
                message_code="payment_reference_unavailable",
                unique_dict={},
            ) from None
        return payment

    async def review(
        self, id: int, status: PaymentStatus, *, reviewer_id: int
    ) -> PaymentModel | None:
        """Update only an existing pending transfer.

        Args:
            id: Stored payment identity.
            status: Prepared review outcome.
            reviewer_id: Authorized reviewer identity recorded for history.

        Returns:
            The reviewed payment, or None if the pending predicate failed.
        """
        table = self.table
        stmt = (
            update(table)
            .where(
                col(table.id) == id, col(table.status) == PaymentStatus.PENDING
            )
            .values(
                status=status, reviewer_id=reviewer_id, reviewed_at=func.now()
            )
            .returning(table)
            .execution_options(
                populate_existing=True, synchronize_session=False
            )
        )
        result = await self.uow.execute(stmt)
        payment = result.scalar_one_or_none()
        return payment

"""Persist IPG payment attempts through the native PostgreSQL repository."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from sqlalchemy import update
from sqlmodel import col

from ....domain.enums.records import LinkStatus
from ....domain.models.records import PaymentModel
from ....domain.results.link import ProviderLink
from ..tables import IPGPaymentTable


class PaymentRepository(PGPersistenceRepository[PaymentModel]):
    table = IPGPaymentTable

    async def save_link(
        self, id: int, link: ProviderLink
    ) -> PaymentModel | None:
        """Store the outcome only while the payment owns an open attempt.

        Args:
            id: Payment identity.
            link: Materialized provider evidence.

        Returns:
            The updated payment, or None if the attempt is absent or closed.
        """
        table = self.table
        stmt = (
            update(table)
            .where(
                col(table.id) == id,
                col(table.status) == LinkStatus.ISSUING,
            )
            .values(
                status=link.status, reference=link.reference, pay_url=link.url
            )
            .returning(table)
        )
        result = await self.uow.execute(stmt)
        payment = result.scalar_one_or_none()
        return payment

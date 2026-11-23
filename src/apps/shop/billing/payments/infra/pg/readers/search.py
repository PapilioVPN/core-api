"""Select filtered payment pages from PostgreSQL."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)
from papilio.schemas.results import PagedType
from sqlmodel import col

from ....domain.enums.records import PaymentSource, PaymentStatus
from ....domain.models.records import PaymentModel
from ..tables import PaymentTable


class PaymentReader(PGIdentifiedRepository[PaymentModel]):
    table = PaymentTable

    async def search(
        self,
        *,
        limit: int,
        offset: int,
        customer_id: int | None,
        source: PaymentSource | None,
        source_id: int | None,
        status: PaymentStatus | None,
    ) -> PagedType[PaymentModel]:
        """Read a filtered page in descending payment ID order.

        Args:
            limit: Maximum number of records to return.
            offset: Matching records to skip.
            customer_id: Optional exact customer identity.
            source: Optional purpose of the payment.
            source_id: Optional identity from the owning payment flow.
            status: Optional exact payment state.

        Returns:
            The matching payments and total before pagination.
        """
        table = self.table
        where = []
        if customer_id is not None:
            where.append(col(table.customer_id) == customer_id)
        if source is not None:
            where.append(col(table.source) == source)
        if source_id is not None:
            where.append(col(table.source_id) == source_id)
        if status is not None:
            where.append(col(table.status) == status)
        page = await self.get_page(
            where=where,
            order_by=[col(table.id).desc()],
            limit=limit,
            offset=offset,
        )
        return page

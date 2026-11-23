"""Read filtered customer payment pages from PostgreSQL."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)
from papilio.schemas.results import PagedType
from sqlmodel import col

from ....domain.enums.records import PaymentStatus
from ....domain.models.records import PaymentModel
from ..tables import PaymentTable


class PaymentReader(PGIdentifiedRepository[PaymentModel]):
    table = PaymentTable

    async def search(
        self,
        *,
        limit: int,
        offset: int,
        q: str | None,
        customer_id: int | None,
        card_id: int | None,
        status: PaymentStatus | None,
    ) -> PagedType[PaymentModel]:
        """Read a filtered page in descending payment ID order.

        Args:
            limit: Maximum rows to return.
            offset: Matching rows to skip.
            q: Optional literal substring of the bank reference.
            customer_id: Optional exact customer identity.
            card_id: Optional exact configured card identity.
            status: Optional exact review state.

        Returns:
            The matching payments and unpaged total.
        """
        table = self.table
        where = []
        if q is not None:
            where.append(col(table.reference).icontains(q, autoescape=True))
        if customer_id is not None:
            where.append(col(table.customer_id) == customer_id)
        if card_id is not None:
            where.append(col(table.card_id) == card_id)
        if status is not None:
            where.append(col(table.status) == status)
        page = await self.get_page(
            where=where,
            order_by=[col(table.id).desc()],
            limit=limit,
            offset=offset,
        )
        return page

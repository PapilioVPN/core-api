"""Read payment pages and payment references through native PostgreSQL."""

from datetime import datetime

from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)
from papilio.schemas.results import PagedType
from sqlalchemy.sql import ColumnElement
from sqlmodel import col

from ....domain.enums.records import PaymentStatus
from ....domain.models.records import PaymentModel
from ..tables import PaymentTable


class PaymentReader(PGIdentifiedRepository[PaymentModel]):
    table = PaymentTable

    async def find_by_receipt_id(self, receipt_id: int) -> PaymentModel | None:
        """Read the payment that owns a receipt.

        Args:
            receipt_id: Stored receipt identity.

        Returns:
            The associated payment, or None when absent.
        """
        payment = await self.get_one(col(self.table.receipt_id) == receipt_id)
        return payment

    async def search(
        self,
        *,
        limit: int,
        offset: int = 0,
        status: PaymentStatus | None = None,
        amount: int | None = None,
        receipt_id: int | None = None,
        created_since: datetime | None = None,
        created_until: datetime | None = None,
    ) -> PagedType[PaymentModel]:
        """Read matching payments in descending identity order.

        Args:
            limit: Maximum number of payments to return.
            offset: Matching payments to skip.
            status: Exact payment state.
            amount: Exact expected amount in rials.
            receipt_id: Exact receipt identity.
            created_since: Inclusive payment creation time bound.
            created_until: Exclusive payment creation time bound.

        Returns:
            Matching payments and the count before pagination.
        """
        table = self.table
        where: list[ColumnElement[bool]] = []
        if status is not None:
            where.append(col(table.status) == status)
        if amount is not None:
            where.append(col(table.amount) == amount)
        if receipt_id is not None:
            where.append(col(table.receipt_id) == receipt_id)
        if created_since is not None:
            where.append(col(table.created_at) >= created_since)
        if created_until is not None:
            where.append(col(table.created_at) < created_until)
        page = await self.get_page(
            where=where,
            order_by=[col(table.id).desc()],
            limit=limit,
            offset=offset,
        )
        return page

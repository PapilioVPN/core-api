"""Read filtered pages of bank receipts through native PostgreSQL."""

from datetime import datetime

from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)
from papilio.schemas.results import PagedType
from sqlalchemy import or_
from sqlalchemy.sql import ColumnElement
from sqlmodel import col

from ....domain.enums.records import ReceiptStatus
from ....domain.models.records import ReceiptModel
from ..tables import ReceiptTable


class ReceiptReader(PGIdentifiedRepository[ReceiptModel]):
    table = ReceiptTable

    async def search(
        self,
        *,
        limit: int,
        offset: int = 0,
        status: ReceiptStatus | None = None,
        amount: int | None = None,
        code: str | None = None,
        paid_since: datetime | None = None,
        paid_until: datetime | None = None,
    ) -> PagedType[ReceiptModel]:
        """Read matching receipts in descending identity order.

        Args:
            limit: Maximum number of receipts to return.
            offset: Matching receipts to skip.
            status: Exact receipt review state.
            amount: Exact observed amount in rials.
            code: Exact tracking or reference code, including leading zeros.
            paid_since: Inclusive bank transaction time bound.
            paid_until: Exclusive bank transaction time bound.

        Returns:
            Matching receipts and the count before pagination.
        """
        table = self.table
        where: list[ColumnElement[bool]] = []
        if status is not None:
            where.append(col(table.status) == status)
        if amount is not None:
            where.append(col(table.amount) == amount)
        if code is not None:
            where.append(
                or_(
                    col(table.tracking_code) == code,
                    col(table.reference_code) == code,
                )
            )
        if paid_since is not None:
            where.append(col(table.paid_at) >= paid_since)
        if paid_until is not None:
            where.append(col(table.paid_at) < paid_until)
        page = await self.get_page(
            where=where,
            order_by=[col(table.id).desc()],
            limit=limit,
            offset=offset,
        )
        return page

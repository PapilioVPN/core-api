"""Bank reference records and filtered pages through native PostgreSQL."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.schemas.results import PagedType
from sqlalchemy import or_
from sqlmodel import col

from ....domain.models.records import BankModel
from ..tables import BankTable


class BankRepository(PGPersistenceRepository[BankModel]):
    table = BankTable

    async def list(
        self, *, limit: int, offset: int, q: str | None, is_active: bool | None
    ) -> PagedType[BankModel]:
        """Read a bank reference page for the administrator panel.

        Args:
            limit: Maximum number of rows to retrieve.
            offset: Matching rows to skip.
            q: Optional literal substring of the bank title or code.
            is_active: Optional issuer activity filter.

        Returns:
            Rows ordered by priority and ID with their unpaged count.
        """
        table = self.table
        where = []
        if q is not None:
            where.append(
                or_(
                    col(table.title).icontains(q, autoescape=True),
                    col(table.code).icontains(q, autoescape=True),
                )
            )
        if is_active is not None:
            where.append(col(table.is_active).is_(is_active))
        page = await self.get_page(
            where=where,
            order_by=[col(table.priority).asc(), col(table.id).asc()],
            limit=limit,
            offset=offset,
        )
        return page

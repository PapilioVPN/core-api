"""Read bank references and resolve indexed card prefixes."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)
from papilio.schemas.results import PagedType
from sqlalchemy import or_, select
from sqlmodel import col

from src.apps.shop.banking.card_prefixes.infra.pg.sql.match import match_prefix

from ....domain.models.records import BankModel
from ....domain.results.prefix import BankMatch
from ..tables import BankTable


class BankReader(PGIdentifiedRepository[BankModel]):
    table = BankTable

    async def find_by_prefix(self, prefix: str) -> BankMatch | None:
        """Resolve a card prefix, preferring an eight-digit match.

        Args:
            prefix: Six or eight ASCII digits from the card number.

        Returns:
            The matching issuer, including historical banks, or None.
        """
        match = match_prefix(prefix[:6], prefix).subquery()
        stmt = select(BankTable, match.c.is_active).join(
            match, match.c.bank_id == col(BankTable.id)
        )
        result = await self.uow.execute(stmt)
        row = result.tuples().one_or_none()
        return BankMatch(*row) if row is not None else None

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

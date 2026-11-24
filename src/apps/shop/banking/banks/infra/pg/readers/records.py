"""Resolve bank references through indexed card prefixes."""

from papilio.infra.db.repositories.backends.postgresql import PGReader
from sqlalchemy import select
from sqlmodel import col

from src.apps.shop.banking.card_prefixes.infra.pg.sql.match import match_prefix

from ....domain.results.prefix import BankMatch
from ..tables import BankTable


class BankPrefixReader(PGReader):
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

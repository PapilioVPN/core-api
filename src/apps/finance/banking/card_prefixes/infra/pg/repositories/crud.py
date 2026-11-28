"""Card prefix storage through Papilio's native PostgreSQL repository."""

from collections.abc import Sequence

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.schemas.results import PagedType
from sqlalchemy.sql import ColumnElement
from sqlmodel import col

from src.apps.finance.banking.card_prefixes.domain.models.records import (
    CardPrefixModel,
)
from src.apps.finance.banking.card_prefixes.infra.pg.tables import (
    CardPrefixTable,
)


class CardPrefixRepository(PGPersistenceRepository[CardPrefixModel]):
    table = CardPrefixTable

    async def find_by_prefix(self, prefix: str) -> CardPrefixModel | None:
        """Read one record by its exact stored prefix.

        Args:
            prefix: Trusted prefix text, preserving leading zeros and length.

        Returns:
            The stored prefix including inactive records; None when absent.
            No card-number parsing or prefix-length inference is performed.
        """
        record = await self.get_one(col(self.table.prefix) == prefix)
        return record

    async def get_by_prefixes(
        self, prefixes: Sequence[str]
    ) -> Sequence[CardPrefixModel]:
        """Read a bounded prefix set through one native selection.

        Args:
            prefixes: Trusted exact prefix strings; duplicates are accepted.

        Returns:
            Unique stored matches including inactive records, omitting missing
            prefixes. Order is unspecified. Empty input performs no I/O.
        """
        records: Sequence[CardPrefixModel] = []
        if prefixes:
            records = await self.get_all(col(self.table.prefix).in_(prefixes))
        return records

    async def list(
        self,
        *,
        limit: int,
        offset: int = 0,
        bank_id: int | None = None,
        is_active: bool | None = None,
    ) -> PagedType[CardPrefixModel]:
        """Read a filtered prefix page in ascending ID order.

        Args:
            limit: Positive maximum number of records to retrieve.
            offset: Nonnegative number of matching records to skip.
            bank_id: Exact parent filter; None includes all banks.
            is_active: Stored activity filter; None includes both states.

        Returns:
            Materialized records and the filtered total before pagination.
            Empty pages retain their total. No transaction is committed.

        Raises:
            ValueError: Native paging rejects invalid retrieval bounds.
        """
        where: list[ColumnElement[bool]] = []
        if bank_id is not None:
            where.append(col(self.table.bank_id) == bank_id)
        if is_active is not None:
            where.append(col(self.table.is_active).is_(is_active))
        page = await self.get_page(
            where=where,
            order_by=[col(self.table.id).asc()],
            limit=limit,
            offset=offset,
        )
        return page

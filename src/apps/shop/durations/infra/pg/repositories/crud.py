"""Native PostgreSQL persistence for duration definitions."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)
from papilio.schemas.results import PagedType
from sqlalchemy import text, true
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col

from src.apps.shop.durations.domain.enums.start import DurationStart
from src.apps.shop.durations.domain.models.records import DurationModel
from src.apps.shop.durations.infra.pg.tables import DurationTable


class DurationRepository(PGIdentifiedRepository[DurationModel]):
    table = DurationTable

    async def insert(self, data: DurationModel) -> DurationModel | None:
        """Try to insert a canonical duration.

        Args:
            data: Validated validity rule, with no identity assigned.

        Returns:
            The new row, or None if its terms already have a canonical row.
        """
        table = self.table
        stmt = (
            insert(table)
            .values(data.to_row())
            .on_conflict_do_nothing(
                index_elements=[col(table.days), col(table.starts_on)],
                index_where=text("is_canonical"),
            )
            .returning(table)
        )
        result = await self.uow.execute(stmt)
        duration = result.scalar_one_or_none()
        return duration

    async def find_by_terms(
        self, days: int, starts_on: DurationStart
    ) -> DurationModel | None:
        """Read the canonical row for an exact duration and start event."""
        table = self.table
        duration = await self.get_one(
            col(table.is_canonical) == true(),
            col(table.days) == days,
            col(table.starts_on) == starts_on,
        )
        return duration

    async def list(
        self,
        *,
        limit: int,
        offset: int = 0,
        days: int | None = None,
        min_days: int | None = None,
        max_days: int | None = None,
    ) -> PagedType[DurationModel]:
        """Read an ID-ordered page with optional duration filters.

        Args:
            limit: Maximum number of rows.
            offset: Number of matching rows to skip.
            days: Exact validity period, in days.
            min_days: Optional inclusive lower bound, in days.
            max_days: Optional inclusive upper bound, in days.

        Returns:
            Matching rows and the total before pagination.
        """
        table = self.table
        where = []
        if days is not None:
            where.append(col(table.days) == days)
        if min_days is not None:
            where.append(col(table.days) >= min_days)
        if max_days is not None:
            where.append(col(table.days) <= max_days)
        page = await self.get_page(
            order_by=[col(table.id).asc()],
            limit=limit,
            offset=offset,
            where=where,
        )
        return page

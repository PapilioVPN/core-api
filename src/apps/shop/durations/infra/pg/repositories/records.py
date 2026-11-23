"""Native PostgreSQL persistence for duration definitions."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)
from papilio.schemas.results import PagedType
from sqlalchemy import select, true
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col

from src.apps.shop.durations.domain.models.records import DurationModel
from src.apps.shop.durations.infra.pg.tables import DurationTable


class DurationRepository(PGIdentifiedRepository[DurationModel]):
    table = DurationTable

    async def save(self, data: DurationModel) -> DurationModel:
        """Insert one definition or return its existing canonical row.

        Args:
            data: Validated validity rule, with no identity assigned.

        Returns:
            The canonical row under the shared terms, with its original ID.
        """
        table = self.table
        stmt = (
            insert(table)
            .values(data.to_row())
            .on_conflict_do_nothing()
            .returning(table)
        )
        result = await self.uow.execute(stmt)
        duration = result.scalar_one_or_none()
        if duration is None:
            stmt = select(table).where(
                col(table.is_canonical) == true(),
                col(table.days) == data.days,
                col(table.starts_on) == data.starts_on,
            )
            result = await self.uow.execute(stmt)
            duration = result.scalar_one()
        return duration

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        days: int | None,
        min_days: int | None,
        max_days: int | None,
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

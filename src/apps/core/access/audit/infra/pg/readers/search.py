"""Read audit history and current filter options directly from PostgreSQL."""

from papilio.infra.db.repositories.backends.postgresql import PGReader
from papilio.infra.db.tools.read import fetch_page
from papilio.schemas.results import PagedType
from sqlalchemy import func, select
from sqlmodel import col

from src.apps.core.access.audit.domain.dtos.search import AuditSearch
from src.apps.core.access.audit.domain.enums.actions import AuditAction
from src.apps.core.access.audit.domain.models.records import AuditModel
from src.apps.core.access.audit.domain.results.filters import AuditOptions
from src.apps.core.access.audit.infra.pg.sql.search import (
    match,
    select_records,
)
from src.apps.core.access.audit.infra.pg.tables import AuditTable


class AuditReader(PGReader):
    async def search(
        self, data: AuditSearch, *, limit: int, offset: int
    ) -> PagedType[AuditModel]:
        """Read a bounded page and its matching total.

        Args:
            data: Original validated filters and sort selection.
            limit: Maximum number of records.
            offset: Number of matching records to skip.

        Returns:
            Ordered records and their total before paging.
        """
        stmt = select_records(data)
        page = await fetch_page(self.uow, stmt, limit=limit, offset=offset)
        return page

    async def get_options(self, q: str | None) -> AuditOptions:
        """Read facet counts over text matches before selected filters.

        Args:
            q: Optional literal search text from the current search.

        Returns:
            Observed actor and action counts and actual time bounds. The bounds
            are absent when no record matches.
        """
        where = match(q)
        actor = col(AuditTable.actor_id)
        stmt = (
            select(actor, func.count())
            .where(where)
            .group_by(actor)
            .order_by(actor)
        )
        actors = await self.uow.execute(stmt)

        action = col(AuditTable.action)
        stmt = (
            select(action, func.count())
            .where(where)
            .group_by(action)
            .order_by(action)
        )
        actions = await self.uow.execute(stmt)

        time = col(AuditTable.created_at)
        stmt = select(func.min(time), func.max(time)).where(where)
        bounds = await self.uow.execute(stmt)
        first, last = bounds.tuples().one()
        return AuditOptions(
            actors=dict(actors.tuples().all()),
            actions={
                AuditAction(key): count for key, count in actions.tuples()
            },
            first=first,
            last=last,
        )

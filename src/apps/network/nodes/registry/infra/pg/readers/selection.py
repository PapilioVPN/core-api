"""Read a projection for the administrator's Node picker."""

from papilio.infra.db.repositories.backends.postgresql import PGReader
from sqlalchemy import select
from sqlmodel import col

from ....domain.results.records import NodeChoice
from ..tables import NodeTable


class NodeSelectionReader(PGReader):
    async def select_choices(
        self,
        *,
        before_id: int | None,
        limit: int,
        q: str | None,
        is_enabled: bool | None,
    ) -> tuple[NodeChoice, ...]:
        """Read one registry projection without an aggregate count.

        Args:
            before_id: Exclusive upper ID bound.
            limit: Maximum rows, including the application's lookahead.
            q: Optional literal substring of the display name.
            is_enabled: Optional registered enabled state.

        Returns:
            Compact choices sorted by decreasing registry ID.
        """
        table = NodeTable
        id, name, enabled = (
            col(table.id),
            col(table.name),
            col(table.is_enabled),
        )
        stmt = select(id, name, enabled)
        if before_id is not None:
            stmt = stmt.where(id < before_id)
        if q is not None:
            stmt = stmt.where(name.icontains(q, autoescape=True))
        if is_enabled is not None:
            stmt = stmt.where(enabled.is_(is_enabled))
        stmt = stmt.order_by(id.desc()).limit(limit)
        result = await self.uow.execute(stmt)
        return tuple(NodeChoice(*row) for row in result.tuples())

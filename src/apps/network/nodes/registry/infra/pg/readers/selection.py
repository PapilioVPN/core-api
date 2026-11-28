"""Read a projection for the administrator's Node picker."""

from papilio.infra.db.repositories.backends.postgresql import PGReader
from sqlalchemy import literal, select, tuple_
from sqlalchemy.orm import aliased
from sqlmodel import col

from src.shared.infra.pg.order import cursor_position, display_position

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
            before_id: Last visible node ID, or None for the first page.
            limit: Maximum rows, including the application's lookahead.
            q: Optional literal substring of the display name.
            is_enabled: Optional registered enabled state.

        Returns:
            Compact choices in the registry display order.
        """
        table = NodeTable
        id, name, enabled = (
            col(table.id),
            col(table.name),
            col(table.is_enabled),
        )
        position = display_position(col(table.sort_order), id)
        stmt = select(id, name, enabled)
        if before_id is not None:
            anchor = aliased(table)
            boundary = cursor_position(
                col(anchor.sort_order), col(anchor.id), before_id
            )
            stmt = stmt.where(
                tuple_(position, id) > tuple_(boundary, literal(before_id))
            )
        if q is not None:
            stmt = stmt.where(name.icontains(q, autoescape=True))
        if is_enabled is not None:
            stmt = stmt.where(enabled.is_(is_enabled))
        stmt = stmt.order_by(position, id).limit(limit)
        result = await self.uow.execute(stmt)
        return tuple(NodeChoice(*row) for row in result.tuples())

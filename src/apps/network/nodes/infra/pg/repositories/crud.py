"""Persist managed node records and query their administrator list."""

from collections.abc import Mapping
from typing import Any

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.schemas.results import PagedType
from sqlalchemy import case, or_
from sqlmodel import col

from ....domain.enums.connection import NodeConnectionStatus
from ....domain.models.records import NodeModel
from ..tables import NodeTable


class NodeRepository(PGPersistenceRepository[NodeModel]):
    table = NodeTable

    async def update_by_id(
        self, id: int, changes: Mapping[str, Any]
    ) -> NodeModel | None:
        """Invalidate checks only when an operator changes the target."""
        table = self.table
        endpoint_fields = {
            "address": col(table.address),
            "port": col(table.port),
            "is_enabled": col(table.is_enabled),
        }
        differences = [
            column.is_distinct_from(changes[key])
            for key, column in endpoint_fields.items()
            if key in changes
        ]
        updates = dict(changes)
        if differences:
            changed = or_(*differences)
            updates.update(
                connection_status=case(
                    (changed, NodeConnectionStatus.UNCHECKED.value),
                    else_=col(table.connection_status),
                ),
                probe_started_at=case(
                    (changed, None), else_=col(table.probe_started_at)
                ),
                last_checked_at=case(
                    (changed, None), else_=col(table.last_checked_at)
                ),
                last_seen_at=case(
                    (changed, None), else_=col(table.last_seen_at)
                ),
            )
        node = await super().update_by_id(id, updates)
        return node

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        q: str | None,
        is_enabled: bool | None,
    ) -> PagedType[NodeModel]:
        """Read a bounded page of managed nodes.

        Args:
            limit: Maximum records to return.
            offset: Number of matching records to skip.
            q: Literal substring of the node's name or management address.
            is_enabled: Optional filter on the operator's enabled state.

        Returns:
            Nodes ordered by descending ID, with the total filtered count.
        """
        table = self.table
        where = []
        if q is not None:
            where.append(
                or_(
                    col(table.name).icontains(q, autoescape=True),
                    col(table.address).icontains(q, autoescape=True),
                )
            )
        if is_enabled is not None:
            where.append(col(table.is_enabled).is_(is_enabled))
        page = await self.get_page(
            where=where,
            order_by=[col(table.id).desc()],
            limit=limit,
            offset=offset,
        )
        return page

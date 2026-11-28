"""Persist managed node records and query their administrator list."""

from collections.abc import Mapping
from typing import Any

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.schemas.results import PagedType
from sqlalchemy import case, or_, select, update
from sqlmodel import col

from src.apps.network.nodes.connections.domain.enums.connection import (
    NodeConnectionStatus,
)
from src.shared.infra.pg.order import (
    display_position,
    display_position_changes,
    lock_display_positions,
)

from ....domain.models.records import NodeModel
from ..tables import NodeTable


class NodeRepository(PGPersistenceRepository[NodeModel]):
    table = NodeTable

    async def lock_sort_positions(
        self, ids: tuple[int, ...]
    ) -> dict[int, int]:
        """Read the current display positions of selected nodes under lock.

        Args:
            ids: Distinct requested node identities.

        Returns:
            Present node IDs and the display positions they occupy.
        """
        table = self.table
        stmt = lock_display_positions(
            col(table.sort_order), col(table.id), ids
        )
        result = await self.uow.execute(stmt)
        return {id: position for id, position in result.tuples()}

    async def set_sort_positions(self, positions: dict[int, int]) -> None:
        """Update the display positions of already locked nodes.

        Args:
            positions: Changed node IDs and their new display positions.
        """
        table = self.table
        ordering = display_position_changes(positions)
        stmt = (
            update(table)
            .where(col(table.id) == ordering.c.id)
            .values(
                sort_order=ordering.c.sort_position,
                updated_at=col(table.updated_at),
            )
            .execution_options(synchronize_session=False)
        )
        await self.uow.execute(stmt)

    async def lock_enabled(self, ids: tuple[int, ...]) -> dict[int, bool]:
        """Read and reserve existing targets in stable registry ID order.

        Args:
            ids: Nonempty set of requested registry identities.

        Returns:
            The current state of each target held by the caller's transaction.
        """
        table = self.table
        id = col(table.id)
        stmt = (
            select(id, col(table.is_enabled))
            .where(id.in_(ids))
            .order_by(id)
            .with_for_update()
        )
        result = await self.uow.execute(stmt)
        return {id: enabled for id, enabled in result.tuples()}

    async def set_enabled(
        self, ids: tuple[int, ...], is_enabled: bool
    ) -> None:
        """Update locked targets and invalidate observations and probe claims.

        Args:
            ids: Locked targets whose enabled state changes.
            is_enabled: The requested enabled state.

        Returns:
            None.
        """
        table = self.table
        stmt = (
            update(table)
            .where(
                col(table.id).in_(ids),
                col(table.is_enabled).is_distinct_from(is_enabled),
            )
            .values(
                is_enabled=is_enabled,
                connection_revision=col(table.connection_revision) + 1,
                connection_status=NodeConnectionStatus.UNCHECKED,
                probe_started_at=None,
                last_checked_at=None,
                last_seen_at=None,
            )
            .execution_options(synchronize_session=False)
        )
        await self.uow.execute(stmt)

    async def update_by_id(
        self, id: int, changes: Mapping[str, Any]
    ) -> NodeModel | None:
        """Invalidate checks only when an operator changes the target."""
        table = self.table
        address_fields = {
            "address": col(table.address),
            "port": col(table.port),
        }
        credential_fields = {
            "api_key_ciphertext": col(table.api_key_ciphertext),
            "ca_pem": col(table.ca_pem),
        }
        connection_fields = {
            **address_fields,
            **credential_fields,
            "is_enabled": col(table.is_enabled),
        }
        differences = [
            column.is_distinct_from(changes[key])
            for key, column in connection_fields.items()
            if key in changes
        ]
        moved = [
            column.is_distinct_from(changes[key])
            for key, column in address_fields.items()
            if key in changes
        ]
        updates = dict(changes)
        if moved:
            different_address = or_(*moved)
            for key, column in credential_fields.items():
                if key not in updates:
                    updates[key] = case(
                        (different_address, None), else_=column
                    )
        if differences:
            updates["connection_revision"] = case(
                (or_(*differences), col(table.connection_revision) + 1),
                else_=col(table.connection_revision),
            )
        if "default_timeout" in changes:
            differences.append(
                col(table.default_timeout).is_distinct_from(
                    changes["default_timeout"]
                )
            )
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
            Nodes in display order, with the total filtered count.
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
            order_by=[
                display_position(col(table.sort_order), col(table.id)),
                col(table.id).asc(),
            ],
            limit=limit,
            offset=offset,
        )
        return page

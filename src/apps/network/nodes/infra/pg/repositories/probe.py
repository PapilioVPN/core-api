"""Reserve due nodes and fence probe completions in PostgreSQL."""

from datetime import timedelta

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from sqlalchemy import and_, func, or_, tuple_, update
from sqlmodel import col, select

from ....domain.enums.connection import NodeConnectionStatus
from ....domain.models.records import NodeModel
from ....domain.results.probe import NodeProbeClaim, NodeProbeTarget
from ..tables import NodeTable


class NodeProbeRepository(PGPersistenceRepository[NodeModel]):
    table = NodeTable

    async def claim(
        self,
        targets: tuple[NodeProbeTarget, ...],
        *,
        delay: timedelta,
        reclaim_after: timedelta,
        limit: int,
    ) -> tuple[NodeProbeClaim, ...]:
        """Reserve one bounded batch of configured, enabled, due targets.

        Args:
            targets: Allowed identities and exact management endpoints.
            delay: Minimum time between starts on a node.
            reclaim_after: Time before an unfinished attempt can be replaced.
            limit: Maximum rows claimed by this run.

        Returns:
            The selected identities, endpoints and database claim times.
        """
        claims = ()
        if targets:
            table = self.table
            id = col(table.id)
            address = col(table.address)
            port = col(table.port)
            started = col(table.probe_started_at)
            checked = col(table.last_checked_at)
            now = func.statement_timestamp()
            due = (
                select(id)
                .where(
                    col(table.is_enabled),
                    tuple_(id, address, port).in_(
                        [(row.id, row.address, row.port) for row in targets]
                    ),
                    or_(
                        started.is_(None),
                        and_(checked >= started, started <= now - delay),
                        started <= now - reclaim_after,
                    ),
                )
                .order_by(started.nulls_first(), id)
                .limit(limit)
                .with_for_update(skip_locked=True)
            )
            stmt = (
                update(table)
                .where(id.in_(due))
                .values(probe_started_at=now, updated_at=col(table.updated_at))
                .returning(id, address, port, started)
                .execution_options(synchronize_session=False)
            )
            rows = await self.uow.execute(stmt)
            claims = tuple(
                NodeProbeClaim(NodeProbeTarget(id, address, port), started_at)
                for id, address, port, started_at in rows.tuples()
                if started_at is not None
            )
        return claims

    async def complete(
        self, claim: NodeProbeClaim, status: NodeConnectionStatus
    ) -> bool:
        """Record one outcome only for the still-current uncompleted claim."""
        table = self.table
        id = col(table.id)
        checked = col(table.last_checked_at)
        target = claim.target
        now = func.statement_timestamp()
        stmt = (
            update(table)
            .where(
                id == target.id,
                col(table.is_enabled),
                col(table.address) == target.address,
                col(table.port) == target.port,
                col(table.probe_started_at) == claim.started_at,
                or_(checked.is_(None), checked < claim.started_at),
            )
            .values(
                connection_status=status,
                last_checked_at=now,
                last_seen_at=(
                    now
                    if status is NodeConnectionStatus.REACHABLE
                    else col(table.last_seen_at)
                ),
                updated_at=col(table.updated_at),
            )
            .returning(id)
            .execution_options(synchronize_session=False)
        )
        result = await self.uow.execute(stmt)
        recorded = result.scalar_one_or_none() is not None
        return recorded

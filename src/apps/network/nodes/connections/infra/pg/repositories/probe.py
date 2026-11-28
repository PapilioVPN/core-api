"""Reserve due nodes and fence probe completions in PostgreSQL."""

from datetime import timedelta

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from sqlalchemy import and_, func, or_, update
from sqlmodel import col, select

from src.apps.network.nodes.registry.domain.models.records import NodeModel
from src.apps.network.nodes.registry.domain.results.records import NodeEndpoint
from src.apps.network.nodes.registry.infra.pg.tables import NodeTable

from ....domain.enums.connection import NodeConnectionStatus
from ....domain.results.probe import NodeProbeClaim


class NodeProbeRepository(PGPersistenceRepository[NodeModel]):
    table = NodeTable

    async def claim(
        self,
        *,
        delay: timedelta,
        reclaim_after: timedelta,
        limit: int,
    ) -> tuple[NodeProbeClaim, ...]:
        """Reserve a bounded set directly from the registry.

        Args:
            delay: Minimum time between starts on a node.
            reclaim_after: Time before an unfinished attempt can be replaced.
            limit: Maximum rows claimed by this run.

        Returns:
            Materialized endpoints and database claim times.
        """
        table = self.table
        id = col(table.id)
        started = col(table.probe_started_at)
        checked = col(table.last_checked_at)
        now = func.statement_timestamp()
        due = (
            select(id)
            .where(
                col(table.is_enabled),
                col(table.api_key_ciphertext).is_not(None),
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
            .returning(
                id,
                col(table.address),
                col(table.port),
                col(table.is_enabled),
                col(table.connection_revision),
                col(table.api_key_ciphertext),
                col(table.ca_pem),
                col(table.default_timeout),
                started,
            )
            .execution_options(synchronize_session=False)
        )
        result = await self.uow.execute(stmt)
        rows = result.tuples()
        return tuple(
            NodeProbeClaim(NodeEndpoint(*row[:-1]), row[-1])
            for row in rows
            if row[-1] is not None
        )

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
                col(table.connection_revision) == target.connection_revision,
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

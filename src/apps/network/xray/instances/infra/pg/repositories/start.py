"""Persist admission and fenced completion of configured Xray starts."""

from datetime import datetime
from uuid import UUID

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from sqlalchemy import select, tuple_, update
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col

from ....domain.dtos.identity import (
    XrayExecutionKey,
    XrayExecutionRequestKey,
    XrayExecutionTrackingKey,
)
from ....domain.enums.start import (
    XrayExecutionAction,
    XrayStartReason,
    XrayStartState,
)
from ....domain.models.start import XrayStartModel
from ....domain.results.start import XrayStartOutcome
from ..tables import XrayStartTable


class XrayStartRepository(PGPersistenceRepository[XrayStartModel]):
    table = XrayStartTable

    async def insert(self, operation: XrayStartModel) -> XrayStartModel | None:
        """Insert one operation, respecting both admission constraints."""
        stmt = (
            insert(self.table)
            .values(operation.to_row())
            .on_conflict_do_nothing()
            .returning(self.table)
        )
        result = await self.uow.execute(stmt)
        return result.scalar_one_or_none()

    async def insert_many(
        self, operations: tuple[XrayStartModel, ...]
    ) -> tuple[XrayStartModel, ...]:
        """Insert the sorted selection without replacing an existing effect."""
        records: tuple[XrayStartModel, ...] = ()
        if operations:
            stmt = (
                insert(self.table)
                .values([operation.to_row() for operation in operations])
                .on_conflict_do_nothing()
                .returning(self.table)
            )
            result = await self.uow.execute(stmt)
            records = tuple(result.scalars())
        return records

    async def find_request(
        self, node_id: int, instance_id: str, request_key: UUID
    ) -> XrayStartModel | None:
        """Resolve the operation behind a replayed idempotency key."""
        table = self.table
        record = await self.get_one(
            col(table.node_id) == node_id,
            col(table.instance_id) == instance_id,
            col(table.request_key) == request_key,
        )
        return record

    async def find_operation(
        self,
        node_id: int,
        instance_id: str,
        id: int,
        *,
        revision_id: int | None,
        action: XrayExecutionAction,
    ) -> XrayStartModel | None:
        """Read one operation within the specified instance and source."""
        table = self.table
        record = await self.get_one(
            col(table.id) == id,
            col(table.node_id) == node_id,
            col(table.instance_id) == instance_id,
            col(table.revision_id) == revision_id,
            col(table.action) == action,
        )
        return record

    async def find_requests(
        self, keys: tuple[XrayExecutionRequestKey, ...]
    ) -> tuple[XrayStartModel, ...]:
        """Look up only the requested scoped idempotency identities."""
        records: tuple[XrayStartModel, ...] = ()
        if keys:
            table = self.table
            rows = await self.get_all(
                tuple_(
                    col(table.node_id),
                    col(table.instance_id),
                    col(table.request_key),
                ).in_(keys)
            )
            records = tuple(rows)
        return records

    async def find_operations(
        self,
        keys: tuple[XrayExecutionTrackingKey, ...],
        *,
        action: XrayExecutionAction,
        revision_id: int | None,
    ) -> tuple[XrayStartModel, ...]:
        """Match selected operation IDs, target pairs, action and source."""
        records: tuple[XrayStartModel, ...] = ()
        if keys:
            table = self.table
            rows = await self.get_all(
                tuple_(
                    col(table.node_id), col(table.instance_id), col(table.id)
                ).in_(keys),
                col(table.revision_id) == revision_id,
                col(table.action) == action,
            )
            records = tuple(rows)
        return records

    async def expire(
        self, node_id: int, instance_id: str, now: datetime
    ) -> None:
        """Abandon an elapsed claim before admitting a new explicit start."""
        table = self.table
        stmt = (
            update(table)
            .where(
                col(table.node_id) == node_id,
                col(table.instance_id) == instance_id,
                col(table.state) == XrayStartState.RUNNING,
                col(table.deadline_at) <= now,
            )
            .values(
                state=XrayStartState.UNKNOWN,
                reason=XrayStartReason.DISPATCH_EXPIRED,
                finished_at=col(table.deadline_at),
            )
            .execution_options(synchronize_session=False)
        )
        await self.uow.execute(stmt)

    async def expire_many(
        self, keys: tuple[XrayExecutionKey, ...], now: datetime
    ) -> None:
        """Expire stale claims in stable lock order before admitting a set."""
        if keys:
            table = self.table
            stale = (
                select(col(table.id))
                .where(
                    tuple_(col(table.node_id), col(table.instance_id)).in_(
                        keys
                    ),
                    col(table.state) == XrayStartState.RUNNING,
                    col(table.deadline_at) <= now,
                )
                .order_by(col(table.node_id), col(table.instance_id))
                .with_for_update()
            )
            stmt = (
                update(table)
                .where(col(table.id).in_(stale))
                .values(
                    state=XrayStartState.UNKNOWN,
                    reason=XrayStartReason.DISPATCH_EXPIRED,
                    finished_at=col(table.deadline_at),
                )
                .execution_options(synchronize_session=False)
            )
            await self.uow.execute(stmt)

    async def claim(
        self,
        id: int,
        *,
        now: datetime,
        deadline: datetime,
        actions: tuple[XrayExecutionAction, ...],
    ) -> XrayStartModel | None:
        """Claim a queued operation before using its target."""
        table = self.table
        stmt = (
            update(table)
            .where(
                col(table.id) == id,
                col(table.state) == XrayStartState.QUEUED,
                col(table.action).in_(actions),
            )
            .values(
                state=XrayStartState.RUNNING,
                started_at=now,
                deadline_at=deadline,
            )
            .returning(table)
            .execution_options(synchronize_session=False)
        )
        result = await self.uow.execute(stmt)
        return result.scalar_one_or_none()

    async def record_stop(self, id: int, *, now: datetime) -> bool:
        """Record the confirmed stop while this restart still owns dispatch."""
        table = self.table
        stmt = (
            update(table)
            .where(
                col(table.id) == id,
                col(table.action) == XrayExecutionAction.RESTART,
                col(table.state) == XrayStartState.RUNNING,
                col(table.deadline_at) > now,
                col(table.stopped_at).is_(None),
            )
            .values(stopped_at=now)
            .returning(col(table.id))
            .execution_options(synchronize_session=False)
        )
        result = await self.uow.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def finish(
        self, id: int, outcome: XrayStartOutcome, *, now: datetime
    ) -> None:
        """Record outcome only while this operation owns an active attempt."""
        table = self.table
        stmt = (
            update(table)
            .where(
                col(table.id) == id,
                col(table.state) == XrayStartState.RUNNING,
                col(table.deadline_at) > now,
            )
            .values(
                state=outcome.state,
                reason=outcome.reason,
                applied_config_sha256=outcome.applied_config_sha256,
                finished_at=now,
            )
            .execution_options(synchronize_session=False)
        )
        await self.uow.execute(stmt)

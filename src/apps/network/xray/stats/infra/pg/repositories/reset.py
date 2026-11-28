"""Persist and fence tracked Xray technical resets."""

from datetime import datetime
from uuid import UUID

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col

from ....domain.enums.reset import ResetReason, ResetState
from ....domain.models.reset import XrayTrafficResetModel
from ....domain.results.reset import ResetOutcome
from ..tables import XrayTrafficResetTable


class XrayResetRepository(PGPersistenceRepository[XrayTrafficResetModel]):
    table = XrayTrafficResetTable

    async def insert(
        self, operation: XrayTrafficResetModel
    ) -> XrayTrafficResetModel | None:
        """Return the inserted operation when admission permits it."""
        stmt = (
            insert(self.table)
            .values(operation.to_row())
            .on_conflict_do_nothing()
            .returning(self.table)
        )
        result = await self.uow.execute(stmt)
        return result.scalar_one_or_none()

    async def find_request(
        self, node_id: int, instance_id: str, key: UUID
    ) -> XrayTrafficResetModel | None:
        """Read the operation associated with a scoped idempotency key."""
        table = self.table
        operation = await self.get_one(
            col(table.node_id) == node_id,
            col(table.instance_id) == instance_id,
            col(table.request_key) == key,
        )
        return operation

    async def find_operation(
        self, node_id: int, instance_id: str, id: int
    ) -> XrayTrafficResetModel | None:
        """Read the requested operation under its owning Node and instance."""
        table = self.table
        operation = await self.get_one(
            col(table.node_id) == node_id,
            col(table.instance_id) == instance_id,
            col(table.id) == id,
        )
        return operation

    async def expire(
        self, node_id: int, instance_id: str, now: datetime
    ) -> None:
        """Release an elapsed dispatch without allowing it to run again."""
        table = self.table
        stmt = (
            update(table)
            .where(
                col(table.node_id) == node_id,
                col(table.instance_id) == instance_id,
                col(table.state) == ResetState.RUNNING,
                col(table.deadline_at) <= now,
            )
            .values(
                state=ResetState.UNKNOWN,
                reason=ResetReason.DISPATCH_EXPIRED,
                finished_at=col(table.deadline_at),
            )
            .execution_options(synchronize_session=False)
        )
        await self.uow.execute(stmt)

    async def claim(
        self, id: int, *, now: datetime, deadline: datetime
    ) -> XrayTrafficResetModel | None:
        """Commit a single dispatch claim before making an external call."""
        table = self.table
        stmt = (
            update(table)
            .where(col(table.id) == id, col(table.state) == ResetState.QUEUED)
            .values(
                state=ResetState.RUNNING,
                started_at=now,
                deadline_at=deadline,
            )
            .returning(table)
            .execution_options(synchronize_session=False)
        )
        result = await self.uow.execute(stmt)
        return result.scalar_one_or_none()

    async def finish(
        self, id: int, outcome: ResetOutcome, *, now: datetime
    ) -> None:
        """Record the typed per-counter Node evidence under the claim."""
        table = self.table
        stmt = (
            update(table)
            .where(
                col(table.id) == id,
                col(table.state) == ResetState.RUNNING,
                col(table.deadline_at) > now,
            )
            .values(
                counters=list(outcome.counters),
                state=outcome.state,
                reason=outcome.reason,
                finished_at=now,
            )
            .execution_options(synchronize_session=False)
        )
        await self.uow.execute(stmt)

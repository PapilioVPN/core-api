"""Persist admission and fenced completion of configured Xray starts."""

from datetime import datetime
from uuid import UUID

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col

from ....domain.enums.start import XrayStartReason, XrayStartState
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
        self, node_id: int, instance_id: str, id: int
    ) -> XrayStartModel | None:
        """Read one operation within the specified instance and node."""
        table = self.table
        record = await self.get_one(
            col(table.id) == id,
            col(table.node_id) == node_id,
            col(table.instance_id) == instance_id,
        )
        return record

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

    async def claim(
        self, id: int, *, now: datetime, deadline: datetime
    ) -> XrayStartModel | None:
        """Claim a queued operation before using its target."""
        table = self.table
        stmt = (
            update(table)
            .where(
                col(table.id) == id, col(table.state) == XrayStartState.QUEUED
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

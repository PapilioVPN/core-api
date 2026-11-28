"""Persist and fence tracked Xray routing deliveries."""

from datetime import datetime
from uuid import UUID

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col

from ....domain.enums.operation import RoutingFailure, RoutingState
from ....domain.models.operation import XrayRoutingOperationModel
from ....domain.results.operation import RoutingOutcome
from ..tables import XrayRoutingOperationTable


class XrayRoutingOperationRepository(
    PGPersistenceRepository[XrayRoutingOperationModel]
):
    table = XrayRoutingOperationTable

    async def insert(
        self, operation: XrayRoutingOperationModel
    ) -> XrayRoutingOperationModel | None:
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
    ) -> XrayRoutingOperationModel | None:
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
    ) -> XrayRoutingOperationModel | None:
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
                col(table.state) == RoutingState.RUNNING,
                col(table.deadline_at) <= now,
            )
            .values(
                state=RoutingState.UNKNOWN,
                reason=RoutingFailure.DISPATCH_EXPIRED,
                finished_at=col(table.deadline_at),
                ciphertext="",
            )
            .execution_options(synchronize_session=False)
        )
        await self.uow.execute(stmt)

    async def claim(
        self, id: int, *, now: datetime, deadline: datetime
    ) -> XrayRoutingOperationModel | None:
        """Commit a single dispatch claim before making an external call."""
        table = self.table
        stmt = (
            update(table)
            .where(
                col(table.id) == id, col(table.state) == RoutingState.QUEUED
            )
            .values(
                state=RoutingState.RUNNING,
                started_at=now,
                deadline_at=deadline,
            )
            .returning(table)
            .execution_options(synchronize_session=False)
        )
        result = await self.uow.execute(stmt)
        return result.scalar_one_or_none()

    async def finish(
        self, id: int, outcome: RoutingOutcome, *, now: datetime
    ) -> None:
        """Record the effect and discard its private input under the claim."""
        table = self.table
        stmt = (
            update(table)
            .where(
                col(table.id) == id,
                col(table.state) == RoutingState.RUNNING,
                col(table.deadline_at) > now,
            )
            .values(
                state=outcome.state,
                reason=outcome.reason,
                finished_at=now,
                ciphertext="",
            )
            .execution_options(synchronize_session=False)
        )
        await self.uow.execute(stmt)

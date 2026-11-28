"""Persist and lock ordered restart plans in short PostgreSQL transactions."""

from datetime import datetime
from uuid import UUID

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col

from ....domain.enums.rollout import RestartRolloutReason, RestartRolloutState
from ....domain.models.rollout import (
    XrayRestartRolloutModel,
    XrayRestartRolloutTargetModel,
)
from ....domain.models.start import XrayStartModel
from ..tables import (
    XrayRestartRolloutTable,
    XrayRestartRolloutTargetTable,
    XrayStartTable,
)


class RestartRolloutRepository(
    PGPersistenceRepository[XrayRestartRolloutModel]
):
    table = XrayRestartRolloutTable

    async def find_request(self, key: UUID) -> XrayRestartRolloutModel | None:
        result = await self.get_one(col(self.table.request_key) == key)
        return result

    async def insert(
        self, plan: XrayRestartRolloutModel
    ) -> XrayRestartRolloutModel | None:
        stmt = (
            insert(self.table)
            .values(plan.to_row())
            .on_conflict_do_nothing()
            .returning(self.table)
        )
        result = await self.uow.execute(stmt)
        return result.scalar_one_or_none()

    async def add_targets(
        self, targets: tuple[XrayRestartRolloutTargetModel, ...]
    ) -> None:
        stmt = insert(XrayRestartRolloutTargetTable).values(
            [row.to_row() for row in targets]
        )
        await self.uow.execute(stmt)

    async def lock(self, id: int) -> XrayRestartRolloutModel | None:
        stmt = (
            select(self.table)
            .where(col(self.table.id) == id)
            .with_for_update()
        )
        result = await self.uow.execute(stmt)
        return result.scalar_one_or_none()

    async def target(
        self, id: int, position: int
    ) -> XrayRestartRolloutTargetModel | None:
        table = XrayRestartRolloutTargetTable
        stmt = select(table).where(
            col(table.rollout_id) == id, col(table.position) == position
        )
        result = await self.uow.execute(stmt)
        return result.scalar_one_or_none()

    async def lock_operation(self, id: int) -> XrayStartModel | None:
        stmt = (
            select(XrayStartTable)
            .where(col(XrayStartTable.id) == id)
            .with_for_update()
        )
        result = await self.uow.execute(stmt)
        return result.scalar_one_or_none()

    async def attach(self, target_id: int, operation_id: int) -> None:
        table = XrayRestartRolloutTargetTable
        stmt = (
            update(table)
            .where(col(table.id) == target_id)
            .values(operation_id=operation_id)
        )
        await self.uow.execute(stmt)

    async def progress(
        self,
        id: int,
        *,
        position: int,
        state: RestartRolloutState,
        reason: RestartRolloutReason | None,
        finished_at: datetime | None,
    ) -> None:
        table = self.table
        stmt = (
            update(table)
            .where(col(table.id) == id)
            .values(
                position=position,
                state=state,
                reason=reason,
                finished_at=finished_at,
            )
        )
        await self.uow.execute(stmt)

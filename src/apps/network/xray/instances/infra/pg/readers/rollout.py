"""Read one rollout and its linked lifecycle evidence from one snapshot."""

from papilio.infra.db.repositories.backends.postgresql import PGReader
from sqlalchemy import select
from sqlmodel import col

from ....domain.results.rollout import (
    RestartRolloutSnapshot,
    RestartRolloutStep,
)
from ..tables import (
    XrayRestartRolloutTable,
    XrayRestartRolloutTargetTable,
    XrayStartTable,
)


class RestartRolloutReader(PGReader):
    async def read(
        self, revision_id: int, id: int
    ) -> RestartRolloutSnapshot | None:
        plan, target, operation = (
            XrayRestartRolloutTable,
            XrayRestartRolloutTargetTable,
            XrayStartTable,
        )
        stmt = (
            select(plan, target, operation)
            .select_from(plan)
            .join(target, col(target.rollout_id) == col(plan.id))
            .outerjoin(
                operation, col(target.operation_id) == col(operation.id)
            )
            .where(col(plan.revision_id) == revision_id, col(plan.id) == id)
            .order_by(col(target.position))
            .execution_options(populate_existing=True)
        )
        result = await self.uow.execute(stmt)
        rows = result.tuples().all()
        snapshot = None
        if rows:
            snapshot = RestartRolloutSnapshot(
                rows[0][0],
                tuple(RestartRolloutStep(step, op) for _, step, op in rows),
            )
        return snapshot

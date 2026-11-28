"""Manage locally desired revision links without calling Node."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from sqlalchemy import delete, func
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col

from ....domain.models.records import XrayDesiredRevisionModel
from ..tables import XrayDesiredRevisionTable


class XrayAssignmentRepository(
    PGPersistenceRepository[XrayDesiredRevisionModel]
):
    table = XrayDesiredRevisionTable

    async def find(
        self, node_id: int, instance_id: str
    ) -> XrayDesiredRevisionModel | None:
        table = self.table
        row = await self.get_one(
            col(table.node_id) == node_id,
            col(table.instance_id) == instance_id,
        )
        return row

    async def set_revision(
        self, node_id: int, instance_id: str, revision_id: int
    ) -> XrayDesiredRevisionModel:
        """Keep timestamps stable for an exact replay of the desired value."""
        table = self.table
        candidate = insert(table).values(
            node_id=node_id, instance_id=instance_id, revision_id=revision_id
        )
        stmt = candidate.on_conflict_do_update(
            constraint="uq_xray_desired_revision_target",
            set_={
                "revision_id": candidate.excluded.revision_id,
                "updated_at": func.statement_timestamp(),
            },
            where=col(table.revision_id).is_distinct_from(
                candidate.excluded.revision_id
            ),
        ).returning(table)
        result = await self.uow.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            row = await self.find(node_id, instance_id)
        if row is None:
            raise RuntimeError("Desired Xray assignment conflict lost its row")
        return row

    async def clear(self, node_id: int, instance_id: str) -> None:
        table = self.table
        stmt = delete(table).where(
            col(table.node_id) == node_id,
            col(table.instance_id) == instance_id,
        )
        await self.uow.execute(stmt)

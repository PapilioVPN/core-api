"""Record one result per delivered receipt event."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col

from ....domain.models.records import OCRRequestModel
from ..tables import OCRRequestTable


class OCRRequestRepository(PGPersistenceRepository[OCRRequestModel]):
    table = OCRRequestTable

    async def exists_by_event(self, event_id: str) -> bool:
        """Check the completion recorded for a durable event identity."""
        exists = await self.exists(col(self.table.event_id) == event_id)
        return exists

    async def insert(self, data: OCRRequestModel) -> OCRRequestModel | None:
        """Persist a completion, omitting previously processed events."""
        table = self.table
        stmt = (
            insert(table)
            .values(data.to_row())
            .on_conflict_do_nothing(index_elements=[col(table.event_id)])
            .returning(table)
        )
        result = await self.uow.execute(stmt)
        record = result.scalar_one_or_none()
        return record

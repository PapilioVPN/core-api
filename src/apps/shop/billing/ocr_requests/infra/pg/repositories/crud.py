"""Record one result per delivered receipt event."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.schemas.results import PagedType
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import ColumnElement
from sqlmodel import col

from src.apps.shop.billing.receipts.domain.enums.extraction import (
    ExtractionStatus,
)

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

    async def find_by_event(self, event_id: str) -> OCRRequestModel | None:
        """Read the attempt identified by its unique delivery identity.

        Args:
            event_id: Durable identity recorded for the event.

        Returns:
            The matching attempt, or None when absent.
        """
        record = await self.get_one(col(self.table.event_id) == event_id)
        return record

    async def list(
        self,
        *,
        limit: int,
        offset: int = 0,
        receipt_id: int | None = None,
        status: ExtractionStatus | None = None,
    ) -> PagedType[OCRRequestModel]:
        """Read one page of completed attempts in descending identity order.

        Args:
            limit: Maximum number of attempts on the page.
            offset: Number of matching attempts to skip.
            receipt_id: Exact receipt identity when supplied.
            status: Exact extraction outcome when supplied.

        Returns:
            The selected attempts and the count before pagination.
        """
        table = self.table
        where: list[ColumnElement[bool]] = []
        if receipt_id is not None:
            where.append(col(table.receipt_id) == receipt_id)
        if status is not None:
            where.append(col(table.status) == status)
        page = await self.get_page(
            where=where,
            order_by=[col(table.id).desc()],
            limit=limit,
            offset=offset,
        )
        return page

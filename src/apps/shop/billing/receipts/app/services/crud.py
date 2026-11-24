"""Persist prepared receipt records."""

from papilio.infra.db.tools.decorators import transactional
from papilio_tasks.apps.outbox import OutboxWriter
from papilio_tasks.apps.outbox import decorators as outbox

from ...domain.enums.extraction import ExtractionStatus
from ...domain.events.records import ReceiptCreated
from ...domain.models.records import ReceiptModel
from ...domain.results.extraction import ReceiptFields
from ...infra.broker.publishers import receipt_created
from ...infra.pg.repositories.crud import ReceiptRepository


class ReceiptService:
    def __init__(self, repo: ReceiptRepository, outbox: OutboxWriter) -> None:
        """Bind receipt persistence and publication to the same request."""
        self.repo = repo
        self.outbox = outbox

    @transactional
    @outbox.publish(receipt_created, select=ReceiptCreated.from_record)
    async def create(self, data: ReceiptModel) -> ReceiptModel:
        """Register receipt evidence.

        Args:
            data: Prepared receipt with its uploaded image address.

        Returns:
            Stored receipt with its identity and timestamps.
        """
        receipt = await self.repo.create(data)
        return receipt

    async def find_by_id(self, id: int) -> ReceiptModel | None:
        """Read one receipt for a background extraction."""
        receipt = await self.repo.get_by_id(id)
        return receipt

    async def save_extraction(
        self, id: int, status: ExtractionStatus, fields: ReceiptFields
    ) -> None:
        """Apply an extraction outcome inside the caller's transaction."""
        changes: dict[str, int | str] = {"extraction_status": status}
        if fields.amount is not None:
            changes["amount"] = fields.amount
        if fields.tracking_code is not None:
            changes["tracking_code"] = fields.tracking_code
        if fields.reference_code is not None:
            changes["reference_code"] = fields.reference_code
        await self.repo.update_by_id(id, changes)

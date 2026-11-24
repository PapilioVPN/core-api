"""Persist prepared receipt records."""

from papilio.infra.db.tools.decorators import transactional
from papilio_tasks.apps.outbox import OutboxWriter
from papilio_tasks.apps.outbox import decorators as outbox

from ...domain.events.records import ReceiptCreated
from ...domain.models.records import ReceiptModel
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

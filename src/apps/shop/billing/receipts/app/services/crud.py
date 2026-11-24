"""Persist prepared receipt records."""

from papilio.errors.exceptions import ConflictException
from papilio.infra.db.tools.decorators import transactional
from papilio.tools.checks import IDChecks
from papilio_tasks.apps.outbox import OutboxWriter

from ...domain.dtos.review import ReceiptReview
from ...domain.events.review import ReceiptCreated
from ...domain.models.records import ReceiptModel
from ...infra.broker.publishers import receipt_created
from ...infra.pg.repositories.crud import ReceiptRepository


class ReceiptService(IDChecks[ReceiptModel]):
    entity = "Receipt"

    def __init__(self, repo: ReceiptRepository, outbox: OutboxWriter) -> None:
        """Bind receipt persistence and publication to the same request."""
        self.repo = repo
        self.outbox = outbox

    @transactional
    async def create(self, data: ReceiptModel) -> ReceiptModel:
        """Register receipt evidence.

        Args:
            data: Prepared receipt with its uploaded image address.

        Returns:
            Stored receipt with its identity and timestamps.
        """
        receipt = await self.repo.create(data)
        await self.outbox.append(
            receipt_created, ReceiptCreated(receipt_id=receipt.id)
        )
        return receipt

    @transactional
    async def review(self, id: int, data: ReceiptReview) -> ReceiptModel:
        """Apply a manual decision to one pending receipt."""
        receipt = await self.repo.review(id, data.status, reason=data.reason)
        if receipt is None:
            existing = await self.repo.get_by_id(id)
            self._check_for_id_existence(id, existing)
            raise ConflictException(
                message="The receipt has already been reviewed",
                message_code="receipt_already_reviewed",
                unique_dict={"id": id},
            )
        return receipt

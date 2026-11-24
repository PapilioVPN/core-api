"""Persist prepared receipt records."""

from papilio.infra.db.tools.decorators import transactional

from ...domain.models.records import ReceiptModel
from ...infra.pg.repositories.crud import ReceiptRepository


class ReceiptService:
    def __init__(self, repo: ReceiptRepository) -> None:
        """Bind the request's receipt repository."""
        self.repo = repo

    @transactional
    async def create(self, data: ReceiptModel) -> ReceiptModel:
        """Register receipt evidence.

        Args:
            data: Prepared receipt with its uploaded image address.

        Returns:
            Stored receipt with its identity and timestamps.
        """
        receipt = await self.repo.create(data)
        return receipt

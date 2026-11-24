"""Write the prepared receipt through a native transaction."""

from papilio.infra.db.tools.decorators import transactional

from ...domain.dtos.records import ReceiptCreate
from ...domain.models.records import ReceiptModel
from ...infra.pg.repositories.crud import ReceiptRepository


class ReceiptService:
    def __init__(self, repo: ReceiptRepository) -> None:
        self.repo = repo

    @transactional
    async def create(self, data: ReceiptCreate) -> ReceiptModel:
        """Register a receipt referencing an uploaded image.

        Args:
            data: Image address and any reported amount in rials and bank time.

        Returns:
            The persisted receipt and its assigned identity.
        """
        receipt = await self.repo.create(ReceiptModel(**data.to_row()))
        return receipt

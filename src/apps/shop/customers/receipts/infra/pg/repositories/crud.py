"""Native receipt record operations."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from sqlmodel import col

from ....domain.models.records import ReceiptModel
from ..tables import ReceiptTable


class ReceiptRepository(PGPersistenceRepository[ReceiptModel]):
    table = ReceiptTable

    async def has_image(self, url: str) -> bool:
        """Check whether a receipt references the exact storage address.

        Args:
            url: Stable image address.

        Returns:
            Whether a stored receipt references the image.
        """
        exists = await self.exists(col(self.table.image_url) == url)
        return exists

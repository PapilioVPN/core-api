"""Store and read pending customer receipts."""

from papilio.errors.exceptions import NotFoundException
from papilio.infra.db.tools.decorators import transactional
from papilio.tools.checks import IDChecks

from ...domain.models.records import ReceiptModel
from ...infra.pg.repositories.crud import ReceiptRepository


class ReceiptCRUD(IDChecks[ReceiptModel]):
    entity = "Receipt"

    def __init__(self, repo: ReceiptRepository) -> None:
        """Bind the receipt repository.

        Args:
            repo: Native PostgreSQL receipt repository.

        Returns:
            None.
        """
        self.repo = repo

    @transactional
    async def create(self, data: ReceiptModel) -> ReceiptModel:
        """Store a pending receipt.

        Args:
            data: Prepared customer identity, rial amount and file address.

        Returns:
            The committed receipt.
        """
        receipt = await self.repo.create(data)
        return receipt

    async def get_by_id(self, id: int) -> ReceiptModel:
        """Read a receipt by identity.

        Args:
            id: Stored receipt identity.

        Returns:
            The receipt and recorded image address.

        Raises:
            NotFoundException: The receipt does not exist.
        """
        receipt = await self.repo.get_by_id(id)
        return self._check_for_id_existence(id, receipt)

    @transactional
    async def check_image(self, url: str) -> None:
        """Require a stored receipt before serving its image.

        Args:
            url: Exact image address derived from the protected route.

        Returns:
            None.

        Raises:
            NotFoundException: No receipt references the image.
        """
        if not await self.repo.has_image(url):
            raise NotFoundException(
                message="Receipt image not found.",
                message_code="receipt_image_not_found",
                entity="Receipt",
                identifier="image_url",
                identifier_value=url,
            )

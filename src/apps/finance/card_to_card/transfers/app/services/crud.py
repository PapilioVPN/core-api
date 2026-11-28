"""Record and read incoming transfers independently of payments."""

from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks
from papilio.types.constants import INT64_MAX

from ...domain.dtos.records import TransferList
from ...domain.models.records import TransferModel
from ...infra.pg.repositories.crud import TransferRepository


class TransferService(IDChecks[TransferModel]):
    entity = "CardTransfer"

    def __init__(self, repo: TransferRepository) -> None:
        self.repo = repo

    async def create(self, data: TransferModel) -> TransferModel:
        """Store a prepared record in the calling command's transaction.

        Args:
            data: Transfer with authenticated provenance and a resolved card
                identity when a destination was supplied.

        Returns:
            The stored transfer with its assigned identity.
        """
        transfer = await self.repo.create(data)
        return transfer

    async def list(self, data: TransferList) -> PagedType[TransferModel]:
        """Read transfers filtered by exact amount, source or card.

        Args:
            data: Validated filters and paging inputs.

        Returns:
            A bounded page of immutable records and its total count.
        """
        page = await self.repo.list(
            amount=data.amount,
            source=data.source,
            card_id=data.card_id,
            limit=data.per_page,
            offset=min((data.page - 1) * data.per_page, INT64_MAX),
        )
        return page

    async def get_by_id(self, id: int) -> TransferModel:
        """Read one recorded incoming transfer.

        Args:
            id: Stored transfer identity.

        Returns:
            The stored transfer.

        Raises:
            NotFoundException: The transfer does not exist.
        """
        transfer = await self.repo.get_by_id(id)
        return self._check_for_id_existence(id, transfer)

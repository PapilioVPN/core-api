"""Store and read payment cards with native PostgreSQL operations."""

from collections.abc import Sequence

from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks

from ...domain.dtos.records import CardList
from ...domain.models.records import PaymentCardModel
from ...infra.pg.repositories.crud import PaymentCardRepository


class PaymentCardService(IDChecks[PaymentCardModel]):
    entity = "PaymentCard"

    def __init__(self, repo: PaymentCardRepository) -> None:
        """Bind card persistence to the request.

        Args:
            repo: Native PostgreSQL card repository.

        Returns:
            None.
        """
        self.repo = repo

    async def create(self, data: PaymentCardModel) -> PaymentCardModel:
        """Store a card in the calling command transaction.

        Args:
            data: Issuer-checked card and its initial settings.

        Returns:
            The stored card.

        Raises:
            ConflictException: Another card uses the number.
        """
        card = await self.repo.create(data)
        return card

    async def get_by_id(self, id: int) -> PaymentCardModel:
        """Read a receiving card by identity.

        Args:
            id: Stored card identity.

        Returns:
            The matching card and its settings.

        Raises:
            NotFoundException: The card does not exist.
        """
        card = await self.repo.get_by_id(id)
        card = self._check_for_id_existence(id, card)
        return card

    async def get_by_ids(
        self, ids: Sequence[int]
    ) -> Sequence[PaymentCardModel]:
        """Read several receiving cards.

        Args:
            ids: Bounded sequence of stored identities.

        Returns:
            Unique matches, omitting missing identities.
        """
        cards = await self.repo.get_by_ids(ids) if ids else []
        return cards

    async def list(self, query: CardList) -> PagedType[PaymentCardModel]:
        """Read one filtered page for the administrator panel.

        Args:
            query: Validated search, filters and paging inputs.

        Returns:
            The page of matching cards and its unpaged count.
        """
        page = await self.repo.list(
            limit=query.per_page,
            offset=(query.page - 1) * query.per_page,
            q=query.q,
            bank_id=query.bank_id,
            is_active=query.is_active,
            allow_manual=query.allow_manual,
            allow_auto=query.allow_auto,
        )
        return page

    async def update(
        self, id: int, data: PaymentCardModel
    ) -> PaymentCardModel:
        """Apply supplied fields in the calling command transaction.

        Args:
            id: Stored card identity.
            data: Changes prepared by the card command.

        Returns:
            The stored card with the patch applied.

        Raises:
            ValidationException: The patch has no recognized fields.
            ConflictException: Another card uses the supplied number.
            NotFoundException: The card does not exist.
        """
        changes = self._check_not_empty_dict(data.to_changes())
        card = await self.repo.update_by_id(id, changes)
        card = self._check_for_id_existence(id, card)
        return card

    @transactional
    async def remove(self, id: int) -> PaymentCardModel:
        """Remove a receiving card.

        Args:
            id: Stored card identity.

        Returns:
            The removed card.

        Raises:
            NotFoundException: The card does not exist.
        """
        card = await self.repo.remove_by_id(id)
        card = self._check_for_id_existence(id, card)
        return card

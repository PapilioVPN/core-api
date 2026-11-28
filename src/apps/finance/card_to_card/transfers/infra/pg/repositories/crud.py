"""Use native PostgreSQL persistence for incoming transfer records."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)
from papilio.schemas.results import PagedType
from sqlalchemy.sql import ColumnElement
from sqlmodel import col

from ....domain.enums.records import TransferSource
from ....domain.models.records import TransferModel
from ..tables import CardTransferTable


class TransferRepository(PGIdentifiedRepository[TransferModel]):
    table = CardTransferTable

    async def list(
        self,
        *,
        amount: int | None,
        source: TransferSource | None,
        card_id: int | None,
        limit: int,
        offset: int,
    ) -> PagedType[TransferModel]:
        """Read matching transfers in newest-first identity order.

        Args:
            amount: Optional exact amount in whole rials.
            source: Optional exact intake source.
            card_id: Optional destination card identity.
            limit: Maximum rows to return.
            offset: Matching rows to skip.

        Returns:
            One page of matching transfers and its unpaged count.
        """
        table = self.table
        where: list[ColumnElement[bool]] = []
        if amount is not None:
            where.append(col(table.amount) == amount)
        if source is not None:
            where.append(col(table.source) == source)
        if card_id is not None:
            where.append(col(table.card_id) == card_id)
        page = await self.get_page(
            where=where,
            order_by=[col(table.id).desc()],
            limit=limit,
            offset=offset,
        )
        return page

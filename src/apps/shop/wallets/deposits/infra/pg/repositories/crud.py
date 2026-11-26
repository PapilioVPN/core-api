"""Persist and read customer-owned top-up requests."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)
from papilio.schemas.results import PagedType
from sqlmodel import col

from ....domain.models.records import WalletDepositModel
from ..tables import WalletDepositTable


class WalletDepositRepository(PGIdentifiedRepository[WalletDepositModel]):
    table = WalletDepositTable

    async def get(
        self, customer_id: int, id: int
    ) -> WalletDepositModel | None:
        """Read one request under its customer.

        Args:
            customer_id: Owning customer identity.
            id: Stored deposit request identity.

        Returns:
            The matching request, or None when absent under this customer.
        """
        table = self.table
        row = await self.get_one(
            col(table.customer_id) == customer_id, col(table.id) == id
        )
        return row

    async def search(
        self, customer_id: int, *, amount: int | None, limit: int, offset: int
    ) -> PagedType[WalletDepositModel]:
        """Page a customer's deposit requests from newest ID to oldest.

        Args:
            customer_id: Owning customer identity.
            amount: Optional exact amount in whole rials.
            limit: Maximum number of requests to return.
            offset: Number of matches to skip.

        Returns:
            The matching page and its total count.
        """
        table = self.table
        where = [col(table.customer_id) == customer_id]
        if amount is not None:
            where.append(col(table.amount) == amount)
        page = await self.get_page(
            where=where,
            order_by=[col(table.id).desc()],
            limit=limit,
            offset=offset,
        )
        return page

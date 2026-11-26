"""Append and read immutable wallet transaction records."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)
from sqlmodel import col

from ....domain.models.records import WalletTransactionModel
from ..tables import WalletTransactionTable


class WalletTransactionRepository(
    PGIdentifiedRepository[WalletTransactionModel]
):
    table = WalletTransactionTable

    async def find(
        self, customer_id: int, transaction_id: int
    ) -> WalletTransactionModel | None:
        """Read a transaction by its immutable identity within one wallet.

        Args:
            customer_id: Owning customer identity.
            transaction_id: Stored transaction identity.

        Returns:
            The matching transaction, or None if it has not posted.
        """
        row = await self.get_one(
            col(self.table.customer_id) == customer_id,
            col(self.table.id) == transaction_id,
        )
        return row

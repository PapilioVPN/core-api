"""Read wallet movements by transaction ID and owner."""

from typing import Protocol

from ...domain.models.records import WalletTransactionModel


class IWalletTransactionService(Protocol):
    async def find(
        self, customer_id: int, transaction_id: int
    ) -> WalletTransactionModel | None: ...

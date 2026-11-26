"""Own persisted wallet transaction records."""

from ...domain.models.records import WalletTransactionModel
from ...infra.pg.repositories.crud import WalletTransactionRepository


class WalletTransactionService:
    def __init__(self, repo: WalletTransactionRepository) -> None:
        """Bind the wallet transaction repository."""
        self.repo = repo

    async def create(
        self, data: WalletTransactionModel
    ) -> WalletTransactionModel:
        """Append the movement prepared inside the balance transaction.

        Args:
            data: Posted amount and the before and after balances.

        Returns:
            The recorded movement with its generated identity.
        """
        row = await self.repo.create(data)
        return row

    async def find(
        self, customer_id: int, transaction_id: int
    ) -> WalletTransactionModel | None:
        """Read a previously posted movement for the supplied wallet.

        Args:
            customer_id: Trusted owning customer identity.
            transaction_id: Stored transaction identity.

        Returns:
            The posted transaction, or None when no matching one exists.
        """
        row = await self.repo.find(customer_id, transaction_id)
        return row

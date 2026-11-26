"""Own persisted wallet transaction records."""

from ...domain.models.records import WalletTransactionModel
from ...infra.pg.repositories.crud import WalletTransactionRepository


class WalletTransactionService:
    def __init__(self, repo: WalletTransactionRepository) -> None:
        """Bind the wallet transaction repository."""
        self.repo = repo

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

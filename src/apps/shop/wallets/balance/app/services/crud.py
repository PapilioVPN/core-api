"""Own wallet opening and balance operations."""

from papilio.infra.db.tools.decorators import transactional
from papilio.tools.checks import Checks

from src.apps.shop.customers.profiles.app.interfaces.services import (
    ICustomerService,
)

from ...domain.models.records import WalletBalanceModel
from ...infra.pg.repositories.crud import WalletBalanceRepository


class WalletBalanceService(Checks[WalletBalanceModel]):
    entity = "WalletBalance"

    def __init__(
        self, repo: WalletBalanceRepository, customers: ICustomerService
    ) -> None:
        """Bind the wallet repository and current customer records."""
        self.repo = repo
        self.customers = customers

    async def find(self, customer_id: int) -> WalletBalanceModel | None:
        """Read a current balance without opening a wallet.

        Args:
            customer_id: Trusted customer identity.

        Returns:
            The current rial balance, or None if the wallet is not open.
        """
        balance = await self.repo.find(customer_id)
        return balance

    async def get(self, customer_id: int) -> WalletBalanceModel:
        """Read a balance for a wallet that must already be open.

        Args:
            customer_id: Trusted customer identity.

        Returns:
            The stored balance in rials.

        Raises:
            NotFoundException: The customer has no open wallet.
        """
        balance = await self.repo.find(customer_id)
        return self._check_for_existence("customer_id", customer_id, balance)

    @transactional
    async def open(self, customer_id: int) -> WalletBalanceModel:
        """Open a wallet at zero or return its existing balance.

        Args:
            customer_id: Trusted identity of the owning customer.

        Returns:
            The customer's stored balance in rials.

        Raises:
            NotFoundException: No customer has this identity.
        """
        await self.customers.get_by_id(customer_id)
        balance = await self.repo.create_zero(customer_id)
        if balance is None:
            balance = await self.repo.find(customer_id)
        return self._check_for_existence("customer_id", customer_id, balance)

    async def increase(
        self, customer_id: int, amount: int
    ) -> WalletBalanceModel | None:
        """Increase the balance in the caller's transaction.

        Args:
            customer_id: Owning customer identity.
            amount: Positive amount in whole rials.

        Returns:
            The updated balance, or None if absent or above the BIGINT limit.
        """
        balance = await self.repo.increase(customer_id, amount)
        return balance

    async def decrease(
        self, customer_id: int, amount: int
    ) -> WalletBalanceModel | None:
        """Decrease the balance in the caller's transaction.

        Args:
            customer_id: Owning customer identity.
            amount: Positive amount in whole rials.

        Returns:
            The updated balance, or None if absent or insufficient.
        """
        balance = await self.repo.decrease(customer_id, amount)
        return balance

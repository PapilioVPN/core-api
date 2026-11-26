"""Persist customer wallet balances."""

from papilio.infra.db.repositories.backends.postgresql import PGRepository
from papilio.types.constants import INT64_MAX
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col

from ....domain.models.records import WalletBalanceModel
from ..tables import WalletBalanceTable


class WalletBalanceRepository(PGRepository[WalletBalanceModel]):
    table = WalletBalanceTable

    async def find(self, customer_id: int) -> WalletBalanceModel | None:
        """Read a customer's current balance.

        Args:
            customer_id: Stored customer identity.

        Returns:
            The stored balance in rials, or None if the wallet is not open.
        """
        balance = await self.get_one(
            col(self.table.customer_id) == customer_id
        )
        return balance

    async def create_zero(self, customer_id: int) -> WalletBalanceModel | None:
        """Create a zero balance without writing to an existing wallet.

        Args:
            customer_id: Stored customer identity.

        Returns:
            The new balance, or None if another row already exists.
        """
        table = self.table
        stmt = (
            insert(table)
            .values(customer_id=customer_id)
            .on_conflict_do_nothing(index_elements=[col(table.customer_id)])
            .returning(table)
        )
        result = await self.uow.execute(stmt)
        balance = result.scalar_one_or_none()
        return balance

    async def increase(
        self, customer_id: int, amount: int
    ) -> WalletBalanceModel | None:
        """Add to the stored wallet balance atomically.

        Args:
            customer_id: Owning customer identity.
            amount: Positive amount in whole rials.

        Returns:
            The updated balance, or None if absent or above the BIGINT limit.
        """
        table = self.table
        current = col(table.amount)
        stmt = (
            update(table)
            .where(
                col(table.customer_id) == customer_id,
                current <= INT64_MAX - amount,
            )
            .values(amount=current + amount)
            .returning(table)
            .execution_options(populate_existing=True)
        )
        result = await self.uow.execute(stmt)
        balance = result.scalar_one_or_none()
        return balance

    async def decrease(
        self, customer_id: int, amount: int
    ) -> WalletBalanceModel | None:
        """Subtract from the stored wallet balance atomically.

        Args:
            customer_id: Owning customer identity.
            amount: Positive amount in whole rials.

        Returns:
            The updated balance, or None if absent or insufficient.
        """
        table = self.table
        current = col(table.amount)
        stmt = (
            update(table)
            .where(col(table.customer_id) == customer_id, current >= amount)
            .values(amount=current - amount)
            .returning(table)
            .execution_options(populate_existing=True)
        )
        result = await self.uow.execute(stmt)
        balance = result.scalar_one_or_none()
        return balance

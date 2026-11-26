"""Internal operations for the authoritative wallet balance."""

from typing import Protocol

from ...domain.models.records import WalletBalanceModel


class IWalletBalanceService(Protocol):
    async def find(self, customer_id: int) -> WalletBalanceModel | None: ...

    async def get(self, customer_id: int) -> WalletBalanceModel: ...

    async def open(self, customer_id: int) -> WalletBalanceModel: ...

    async def increase(
        self, customer_id: int, amount: int
    ) -> WalletBalanceModel | None: ...

    async def decrease(
        self, customer_id: int, amount: int
    ) -> WalletBalanceModel | None: ...

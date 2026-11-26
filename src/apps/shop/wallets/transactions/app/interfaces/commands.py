"""Post a movement and update the wallet atomically."""

from typing import Protocol

from ...domain.dtos.records import TransactionPost
from ...domain.models.records import WalletTransactionModel


class IWalletCreditCommand(Protocol):
    async def credit(
        self, customer_id: int, data: TransactionPost
    ) -> WalletTransactionModel: ...


class IWalletDebitCommand(Protocol):
    async def debit(
        self, customer_id: int, data: TransactionPost
    ) -> WalletTransactionModel: ...

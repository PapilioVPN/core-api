"""Coordinate one wallet operation and its balance update."""

from papilio.errors.exceptions import ValidationException
from papilio.infra.db.tools.decorators import transactional

from src.apps.shop.wallets.balance.app.interfaces.services import (
    IWalletBalanceService,
)

from ...domain.dtos.records import TransactionPost
from ...domain.enums.records import Direction
from ...domain.models.records import WalletTransactionModel
from ..interfaces.services import IWalletTransactionService


class WalletCreditCommand:
    def __init__(
        self,
        transactions: IWalletTransactionService,
        balances: IWalletBalanceService,
    ) -> None:
        """Bind the two request-scoped owners of posting and balance."""
        self.transactions = transactions
        self.balances = balances

    @transactional
    async def credit(
        self, customer_id: int, data: TransactionPost
    ) -> WalletTransactionModel:
        """Credit a customer's wallet, opening it in the same transaction.

        Args:
            customer_id: Trusted identity of the owning customer.
            data: Positive rial amount and optional description.

        Returns:
            The posted credit.

        Raises:
            NotFoundException: The customer is absent.
            ValidationException: The credit exceeds the balance limit.
        """
        await self.balances.open(customer_id)
        balance = await self.balances.increase(customer_id, data.amount)
        if balance is None:
            raise ValidationException(
                message="The credit exceeds the wallet balance limit.",
                message_code="wallet_balance_limit",
                loc=["amount"],
                input=data.amount,
            )
        row = await self.transactions.create(
            WalletTransactionModel(
                customer_id=customer_id,
                direction=Direction.CREDIT,
                amount=data.amount,
                balance_before=balance.amount - data.amount,
                balance_after=balance.amount,
                description=data.description,
            )
        )
        return row


class WalletDebitCommand:
    def __init__(
        self,
        transactions: IWalletTransactionService,
        balances: IWalletBalanceService,
    ) -> None:
        """Bind the two request-scoped owners of posting and balance."""
        self.transactions = transactions
        self.balances = balances

    @transactional
    async def debit(
        self, customer_id: int, data: TransactionPost
    ) -> WalletTransactionModel:
        """Debit an open wallet if its current balance covers the amount.

        Args:
            customer_id: Trusted identity of the open wallet's owner.
            data: Positive rial amount and optional description.

        Returns:
            The posted debit.

        Raises:
            NotFoundException: The wallet is not open.
            ValidationException: The wallet has insufficient funds.
        """
        await self.balances.get(customer_id)
        balance = await self.balances.decrease(customer_id, data.amount)
        if balance is None:
            raise ValidationException(
                message="The wallet has insufficient funds.",
                message_code="wallet_insufficient_balance",
                loc=["amount"],
                input=data.amount,
            )
        row = await self.transactions.create(
            WalletTransactionModel(
                customer_id=customer_id,
                direction=Direction.DEBIT,
                amount=data.amount,
                balance_before=balance.amount + data.amount,
                balance_after=balance.amount,
                description=data.description,
            )
        )
        return row

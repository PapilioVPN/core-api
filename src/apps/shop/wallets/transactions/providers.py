"""Bind the wallet journal through native request-scoped providers."""

from dishka import Provider, Scope, provide

from .app.commands.post import WalletCreditCommand, WalletDebitCommand
from .app.interfaces.commands import IWalletCreditCommand, IWalletDebitCommand
from .app.interfaces.services import IWalletTransactionService
from .app.services.crud import WalletTransactionService
from .infra.pg.repositories.crud import WalletTransactionRepository


class WalletTransactionProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(WalletTransactionRepository)
    service = provide(
        WalletTransactionService, provides=IWalletTransactionService
    )
    credit_command = provide(
        WalletCreditCommand, provides=IWalletCreditCommand
    )
    debit_command = provide(WalletDebitCommand, provides=IWalletDebitCommand)

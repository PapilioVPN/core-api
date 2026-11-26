"""Bind the wallet journal through native request-scoped providers."""

from dishka import Provider, Scope, provide

from .app.commands.post import WalletTransactionCommand
from .app.interfaces.commands import IWalletTransactionCommand
from .app.interfaces.services import IWalletTransactionService
from .app.services.crud import WalletTransactionService
from .infra.pg.repositories.crud import WalletTransactionRepository


class WalletTransactionProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(WalletTransactionRepository)
    service = provide(
        WalletTransactionService, provides=IWalletTransactionService
    )
    command = provide(
        WalletTransactionCommand, provides=IWalletTransactionCommand
    )

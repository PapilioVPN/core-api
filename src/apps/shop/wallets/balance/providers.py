"""Bind wallet balances to native request-scoped persistence."""

from dishka import Provider, Scope, provide

from .app.interfaces.services import IWalletBalanceService
from .app.services.crud import WalletBalanceService
from .infra.pg.repositories.crud import WalletBalanceRepository


class WalletBalanceProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(WalletBalanceRepository)
    service = provide(WalletBalanceService, provides=IWalletBalanceService)

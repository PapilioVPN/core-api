"""Bind wallet deposits to native request-scoped persistence."""

from dishka import Provider, Scope, provide

from .app.interfaces.services import IWalletDepositService
from .app.services.crud import WalletDepositService
from .infra.pg.repositories.crud import WalletDepositRepository


class WalletDepositProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(WalletDepositRepository)
    service = provide(WalletDepositService, provides=IWalletDepositService)

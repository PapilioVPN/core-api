"""Bind the wallet top-up flow to the shared Redis client."""

from dishka import Provider, Scope, provide

from .app.commands.issue import WalletDepositCommand
from .app.interfaces.commands import IWalletDepositCommand
from .app.interfaces.queries import IDepositMethodsQuery
from .app.interfaces.services import IWalletDepositService
from .app.queries.methods import DepositMethodsQuery
from .app.services.crud import WalletDepositService
from .infra.redis.cache import WalletDepositCache


class WalletDepositProvider(Provider):
    scope = Scope.REQUEST

    cache = provide(WalletDepositCache, scope=Scope.APP)
    service = provide(WalletDepositService, provides=IWalletDepositService)
    command = provide(WalletDepositCommand, provides=IWalletDepositCommand)
    methods = provide(DepositMethodsQuery, provides=IDepositMethodsQuery)

"""Bind the wallet top-up flow to the shared Redis client."""

from dishka import Provider, Scope, provide

from .app.commands.card import CardInvoiceCommand
from .app.commands.plisio import PlisioInvoiceCommand
from .app.interfaces.commands import ICardInvoiceCommand, IPlisioInvoiceCommand
from .app.interfaces.queries import IDepositMethodsQuery
from .app.interfaces.services import IWalletDepositService
from .app.queries.methods import DepositMethodsQuery
from .app.services.crud import WalletDepositService
from .infra.redis.cache import WalletDepositCache


class WalletDepositProvider(Provider):
    scope = Scope.REQUEST

    cache = provide(WalletDepositCache, scope=Scope.APP)
    service = provide(WalletDepositService, provides=IWalletDepositService)
    card = provide(CardInvoiceCommand, provides=ICardInvoiceCommand)
    plisio = provide(PlisioInvoiceCommand, provides=IPlisioInvoiceCommand)
    methods = provide(DepositMethodsQuery, provides=IDepositMethodsQuery)

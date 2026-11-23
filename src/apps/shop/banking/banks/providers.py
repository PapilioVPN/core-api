"""Bind bank reference reads to the native request scope."""

from dishka import Provider, Scope, provide

from .app.interfaces.queries import IBankQuery
from .app.queries.records import BankQuery
from .infra.pg.readers.records import BankReader


class BankProvider(Provider):
    scope = Scope.REQUEST

    reader = provide(BankReader)
    query = provide(BankQuery, provides=IBankQuery)

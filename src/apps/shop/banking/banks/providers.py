"""Bind bank reference reads to the native request scope."""

from dishka import Provider, Scope, provide

from .app.interfaces.queries import IBankQuery
from .app.queries.records import BankQuery
from .infra.pg.readers.records import BankPrefixReader
from .infra.pg.repositories.records import BankRepository


class BankProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(BankRepository)
    prefix_reader = provide(BankPrefixReader)
    query = provide(BankQuery, provides=IBankQuery)

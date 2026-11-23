"""Bind payment registration and reads to the request scope."""

from dishka import Provider, Scope, provide

from .app.commands.records import PaymentCommand
from .app.interfaces.commands import IPaymentCommand
from .app.interfaces.queries import IPaymentSearch
from .app.interfaces.services import IPaymentCRUD
from .app.queries.search import PaymentSearchQuery
from .app.services.crud import PaymentCRUD
from .infra.pg.readers.search import PaymentReader
from .infra.pg.repositories.crud import PaymentRepository


class PaymentProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(PaymentRepository)
    crud = provide(PaymentCRUD, provides=IPaymentCRUD)
    command = provide(PaymentCommand, provides=IPaymentCommand)
    reader = provide(PaymentReader)
    search = provide(PaymentSearchQuery, provides=IPaymentSearch)

"""Bind payment record operations to the request scope."""

from dishka import Provider, Scope, provide

from .app.commands.records import PaymentCommand
from .app.interfaces.commands import IPaymentCommand
from .app.interfaces.queries import IPaymentQuery, IPaymentSearchQuery
from .app.interfaces.services import IPaymentService
from .app.queries.details import PaymentQuery
from .app.queries.search import PaymentSearchQuery
from .app.services.crud import PaymentService
from .infra.pg.readers.details import PaymentReader
from .infra.pg.repositories.crud import PaymentRepository


class PaymentProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(PaymentRepository)
    reader = provide(PaymentReader)
    payments = provide(PaymentService, provides=IPaymentService)
    command = provide(PaymentCommand, provides=IPaymentCommand)
    query = provide(PaymentQuery, provides=IPaymentQuery)
    search = provide(PaymentSearchQuery, provides=IPaymentSearchQuery)

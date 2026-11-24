"""Bind payment record operations to the request scope."""

from dishka import Provider, Scope, provide

from .app.commands.records import PaymentCommand
from .app.interfaces.commands import IPaymentCommand
from .app.interfaces.services import IPaymentService
from .app.services.crud import PaymentService
from .infra.pg.repositories.crud import PaymentRepository


class PaymentProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(PaymentRepository)
    payments = provide(PaymentService, provides=IPaymentService)
    command = provide(PaymentCommand, provides=IPaymentCommand)

"""Bind payment record operations to the native request scope."""

from dishka import Provider, Scope, provide

from .app.commands.create import PaymentCreateCommand
from .app.interfaces.services import ICryptoPaymentService
from .app.services.crud import CryptoPaymentService
from .infra.pg.repositories.crud import CryptoPaymentRepository


class CryptoPaymentProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(CryptoPaymentRepository)
    service = provide(CryptoPaymentService, provides=ICryptoPaymentService)
    create = provide(PaymentCreateCommand)

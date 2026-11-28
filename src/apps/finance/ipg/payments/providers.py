"""Bind IPG payment persistence and shared HTTP clients."""

from dishka import Provider, Scope, provide

from .app.executions.link import LinkExecution
from .app.interfaces.create import (
    ICreatePaymentCommand,
    ILinkExecution,
    IZarinPalClient,
    IZibalClient,
)
from .app.pipelines.link import CreatePaymentCommand
from .app.services.crud import PaymentService
from .infra.pg.repositories.crud import PaymentRepository
from .infra.zarinpal.client import ZarinPalClient
from .infra.zibal.client import ZibalClient


class PaymentsProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(PaymentRepository)
    payments = provide(PaymentService)
    execution = provide(
        LinkExecution, provides=ILinkExecution, scope=Scope.APP
    )
    zarinpal = provide(
        ZarinPalClient, provides=IZarinPalClient, scope=Scope.APP
    )
    zibal = provide(ZibalClient, provides=IZibalClient, scope=Scope.APP)
    create = provide(
        CreatePaymentCommand, provides=ICreatePaymentCommand, scope=Scope.APP
    )

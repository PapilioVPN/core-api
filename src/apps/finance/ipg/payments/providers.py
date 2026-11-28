"""Bind IPG persistence, verification and the async payment SDK."""

from dishka import Provider, Scope, provide

from .app.commands.callback import VerifyCallbackCommand
from .app.executions.link import LinkExecution
from .app.executions.verify import VerifyExecution
from .app.interfaces.callback import IVerifyCallbackCommand
from .app.interfaces.create import (
    ICreatePaymentCommand,
    ILinkExecution,
    IZarinPalClient,
    IZibalClient,
)
from .app.interfaces.services import IPaymentService
from .app.pipelines.link import CreatePaymentCommand
from .app.pipelines.verify import VerifyPipeline
from .app.services.crud import PaymentService
from .infra.pg.repositories.crud import PaymentRepository
from .infra.pg.repositories.verify import VerifyRepository
from .infra.zarinpal.client import ZarinPalClient
from .infra.zibal.client import ZibalClient


class PaymentsProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(PaymentRepository)
    checks = provide(VerifyRepository)
    verify_execution = provide(VerifyExecution, scope=Scope.APP)
    verify = provide(VerifyPipeline, scope=Scope.APP)
    callback = provide(
        VerifyCallbackCommand, provides=IVerifyCallbackCommand, scope=Scope.APP
    )
    payments = provide(PaymentService, provides=IPaymentService)
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

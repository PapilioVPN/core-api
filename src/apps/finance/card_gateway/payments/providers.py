"""Bind hosted payment requests and provider adapters."""

from dishka import Provider, Scope, provide

from .app.commands.confirm import ConfirmPaymentCommand
from .app.executions.link import LinkExecution
from .app.interfaces.commands import IConfirmPaymentCommand
from .app.interfaces.link import (
    ICreateLinkCommand,
    ILinkExecution,
    IVarizaClient,
)
from .app.interfaces.services import IDeliveryService, IPaymentService
from .app.interfaces.webhook import IVarizaWebhookCodec, IVarizaWebhookService
from .app.pipelines.link import LinkPipeline
from .app.services.crud import PaymentService
from .app.services.deliveries import DeliveryService
from .app.services.webhook import VarizaWebhookService
from .infra.pg.repositories.crud import PaymentRepository
from .infra.pg.repositories.deliveries import DeliveryRepository
from .infra.variza.client import VarizaClient
from .infra.variza.webhook import VarizaWebhookCodec


class PaymentsProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(PaymentRepository)
    delivery_repo = provide(DeliveryRepository)
    payments = provide(PaymentService, provides=IPaymentService)
    deliveries = provide(DeliveryService, provides=IDeliveryService)
    webhook_codec = provide(
        VarizaWebhookCodec, provides=IVarizaWebhookCodec, scope=Scope.APP
    )
    webhook = provide(VarizaWebhookService, provides=IVarizaWebhookService)
    confirm = provide(ConfirmPaymentCommand, provides=IConfirmPaymentCommand)
    execution = provide(
        LinkExecution, provides=ILinkExecution, scope=Scope.APP
    )
    variza = provide(VarizaClient, provides=IVarizaClient, scope=Scope.APP)
    create_link = provide(
        LinkPipeline, provides=ICreateLinkCommand, scope=Scope.APP
    )

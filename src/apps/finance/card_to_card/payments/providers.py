"""Bind card payment storage, commands and receipt upload."""

from dishka import Provider, Scope, provide

from .app.commands.auto import AutoPaymentCommand
from .app.commands.auto_confirm import ConfirmTransferCommand
from .app.commands.manual import ManualPaymentCommand
from .app.commands.manual_confirm import ReviewPaymentCommand
from .app.interfaces.commands import (
    IAutoPaymentCommand,
    IConfirmTransferCommand,
    IManualPaymentCommand,
    IReviewPaymentCommand,
)
from .app.interfaces.queries import ICardPaymentQuery
from .app.interfaces.services import ICardPaymentService
from .app.interfaces.uploads import IReceiptUpload
from .app.queries.records import CardPaymentQuery
from .app.services.crud import CardPaymentService
from .app.services.uploads import ReceiptUploadService
from .infra.pg.repositories.crud import CardPaymentRepository


class CardPaymentProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(CardPaymentRepository)
    service = provide(CardPaymentService, provides=ICardPaymentService)
    query = provide(CardPaymentQuery, provides=ICardPaymentQuery)
    auto = provide(AutoPaymentCommand, provides=IAutoPaymentCommand)
    manual = provide(ManualPaymentCommand, provides=IManualPaymentCommand)
    confirm = provide(ConfirmTransferCommand, provides=IConfirmTransferCommand)
    review = provide(ReviewPaymentCommand, provides=IReviewPaymentCommand)
    upload = provide(
        ReceiptUploadService, provides=IReceiptUpload, scope=Scope.APP
    )

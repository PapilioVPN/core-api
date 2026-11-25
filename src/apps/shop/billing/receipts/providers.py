"""Bind receipt record operations to the request scope."""

from dishka import Provider, Scope, provide

from .app.commands.uploads import ReceiptUploadCommand
from .app.interfaces.services import IReceiptService
from .app.interfaces.uploads import IReceiptUpload
from .app.services.crud import ReceiptService
from .infra.pg.repositories.crud import ReceiptRepository


class ReceiptProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(ReceiptRepository)
    receipts = provide(ReceiptService, provides=IReceiptService)
    upload = provide(
        ReceiptUploadCommand, provides=IReceiptUpload, scope=Scope.APP
    )

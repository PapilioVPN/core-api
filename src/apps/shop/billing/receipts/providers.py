"""Bind receipt record operations to the request scope."""

from dishka import Provider, Scope, provide

from .app.commands.review import ReceiptReviewCommand
from .app.interfaces.commands import IReceiptReviewCommand
from .app.interfaces.services import IReceiptService
from .app.interfaces.uploads import IReceiptUpload
from .app.services.crud import ReceiptService
from .app.services.uploads import ReceiptUploadService
from .infra.pg.repositories.crud import ReceiptRepository


class ReceiptProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(ReceiptRepository)
    receipts = provide(ReceiptService, provides=IReceiptService)
    review = provide(ReceiptReviewCommand, provides=IReceiptReviewCommand)
    upload = provide(
        ReceiptUploadService, provides=IReceiptUpload, scope=Scope.APP
    )

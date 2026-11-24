"""Bind receipt image policy and record persistence."""

from dishka import Provider, Scope, provide

from .app.interfaces.images import IReceiptImages
from .app.interfaces.services import IReceiptService
from .app.services.crud import ReceiptService
from .app.services.images import ReceiptImages
from .infra.pg.repositories.crud import ReceiptRepository


class ReceiptProvider(Provider):
    scope = Scope.APP

    images = provide(ReceiptImages, provides=IReceiptImages)


class ReceiptRecordProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(ReceiptRepository)
    service = provide(ReceiptService, provides=IReceiptService)

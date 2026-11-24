"""Bind receipt record operations to the request scope."""

from dishka import Provider, Scope, provide

from .app.interfaces.services import IReceiptService
from .app.services.crud import ReceiptService
from .infra.pg.repositories.crud import ReceiptRepository


class ReceiptProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(ReceiptRepository)
    receipts = provide(ReceiptService, provides=IReceiptService)

"""Bind receipt operations to the native request scope."""

from dishka import Provider, Scope, provide

from .app.commands.records import ReceiptCommand
from .app.interfaces.commands import IReceiptCommand
from .app.interfaces.services import IReceiptCRUD
from .app.services.crud import ReceiptCRUD
from .infra.pg.repositories.crud import ReceiptRepository


class ReceiptProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(ReceiptRepository)
    crud = provide(ReceiptCRUD, provides=IReceiptCRUD)
    command = provide(ReceiptCommand, provides=IReceiptCommand)

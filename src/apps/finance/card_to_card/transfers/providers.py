"""Bind incoming transfer persistence and service contracts."""

from dishka import Provider, Scope, provide

from .app.commands.admin import AdminTransferCommand
from .app.commands.hook import HookTransferCommand
from .app.interfaces.commands import (
    IAdminTransferCommand,
    IHookTransferCommand,
)
from .app.interfaces.services import ITransferService
from .app.services.crud import TransferService
from .infra.pg.repositories.crud import TransferRepository


class CardTransferProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(TransferRepository)
    service = provide(TransferService, provides=ITransferService)
    admin = provide(AdminTransferCommand, provides=IAdminTransferCommand)
    hook = provide(HookTransferCommand, provides=IHookTransferCommand)

"""Bind bank deposit operations to the native request scope."""

from dishka import Provider, Scope, provide

from .app.commands.match import DepositMatchCommand
from .app.commands.records import DepositCommand
from .app.interfaces.services import IDepositService
from .app.services.crud import DepositService
from .infra.pg.repositories.crud import DepositRepository


class DepositProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(DepositRepository)
    deposits = provide(DepositService, provides=IDepositService)
    command = provide(DepositCommand)
    match = provide(DepositMatchCommand)

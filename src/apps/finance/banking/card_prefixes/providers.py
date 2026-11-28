"""Bind card prefix persistence and service to native request scope."""

from dishka import Provider, Scope, provide

from .app.commands.records import (
    CardPrefixCreateCommand,
    CardPrefixUpdateCommand,
)
from .app.interfaces.records import (
    ICardPrefixCreateCommand,
    ICardPrefixService,
    ICardPrefixUpdateCommand,
)
from .app.services.crud import CardPrefixService
from .infra.pg.repositories.crud import CardPrefixRepository


class CardPrefixProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(CardPrefixRepository)
    service = provide(CardPrefixService, provides=ICardPrefixService)
    create_command = provide(
        CardPrefixCreateCommand, provides=ICardPrefixCreateCommand
    )
    update_command = provide(
        CardPrefixUpdateCommand, provides=ICardPrefixUpdateCommand
    )

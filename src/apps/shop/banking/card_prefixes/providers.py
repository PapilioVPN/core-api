"""Bind card prefix persistence and service to native request scope."""

from dishka import Provider, Scope, provide

from .app.commands.records import CardPrefixCommand
from .app.interfaces.records import ICardPrefixCommand, ICardPrefixService
from .app.services.crud import CardPrefixService
from .infra.pg.repositories.crud import CardPrefixRepository


class CardPrefixProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(CardPrefixRepository)
    service = provide(CardPrefixService, provides=ICardPrefixService)
    command = provide(CardPrefixCommand, provides=ICardPrefixCommand)

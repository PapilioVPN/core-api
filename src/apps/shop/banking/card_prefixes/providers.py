"""Bind card prefix persistence and service to native request scope."""

from dishka import Provider, Scope, provide

from .app.commands.records import CardPrefixCommand
from .app.interfaces.records import ICardPrefixCommand, ICardPrefixCRUD
from .app.services.crud import CardPrefixCRUD
from .infra.pg.repositories.crud import CardPrefixRepository


class CardPrefixProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(CardPrefixRepository)
    crud = provide(CardPrefixCRUD, provides=ICardPrefixCRUD)
    command = provide(CardPrefixCommand, provides=ICardPrefixCommand)

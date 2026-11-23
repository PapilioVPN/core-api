"""Bind payment card commands, records and selection to the request scope."""

from dishka import Provider, Scope, provide

from .app.commands.records import CardCommand
from .app.interfaces.commands import ICardCommand
from .app.interfaces.queries import ICardPickQuery
from .app.interfaces.services import ICardCRUD
from .app.services.crud import CardCRUD
from .infra.pg.readers.pick import CardPickReader
from .infra.pg.repositories.crud import CardRepository


class CardProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(CardRepository)
    crud = provide(CardCRUD, provides=ICardCRUD)
    command = provide(CardCommand, provides=ICardCommand)
    pick = provide(CardPickReader, provides=ICardPickQuery)

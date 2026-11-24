"""Bind payment card commands, records and selection to the request scope."""

from dishka import Provider, Scope, provide

from .app.commands.records import CardCommand
from .app.interfaces.commands import ICardCommand
from .app.interfaces.queries import ICardPickQuery
from .app.interfaces.services import IPaymentCardService
from .app.services.crud import PaymentCardService
from .infra.pg.readers.pick import CardPickReader
from .infra.pg.repositories.crud import PaymentCardRepository


class CardProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(PaymentCardRepository)
    service = provide(PaymentCardService, provides=IPaymentCardService)
    command = provide(CardCommand, provides=ICardCommand)
    pick = provide(CardPickReader, provides=ICardPickQuery)

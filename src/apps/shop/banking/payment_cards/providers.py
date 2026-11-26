"""Bind payment card commands, records and selection to the request scope."""

from dishka import Provider, Scope, provide

from .app.commands.records import CardCreateCommand, CardUpdateCommand
from .app.interfaces.commands import ICardCreateCommand, ICardUpdateCommand
from .app.interfaces.queries import ICardPickQuery
from .app.interfaces.services import ICardIssuerService, IPaymentCardService
from .app.services.crud import PaymentCardService
from .app.services.issuer import CardIssuerService
from .infra.pg.readers.pick import CardPickReader
from .infra.pg.repositories.crud import PaymentCardRepository


class CardProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(PaymentCardRepository)
    service = provide(PaymentCardService, provides=IPaymentCardService)
    issuer = provide(CardIssuerService, provides=ICardIssuerService)
    create_command = provide(CardCreateCommand, provides=ICardCreateCommand)
    update_command = provide(CardUpdateCommand, provides=ICardUpdateCommand)
    pick = provide(CardPickReader, provides=ICardPickQuery)

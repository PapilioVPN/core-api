"""Bind the public market adapter and request-owned rate operations."""

from dishka import Provider, Scope, provide
from papilio.infra.http.connection import HTTPConnection

from .app.commands.refresh import RateRefreshCommand
from .app.interfaces.feed import IWallexRate
from .app.interfaces.services import ICryptoRateService
from .app.services.crud import CryptoRateService
from .infra.pg.repositories.crud import CryptoRateRepository
from .infra.wallex.client import WallexRateGateway


class CryptoRateProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(CryptoRateRepository)
    rates = provide(CryptoRateService, provides=ICryptoRateService)
    refresh = provide(RateRefreshCommand)

    @provide(scope=Scope.APP)
    def feed(self, connection: HTTPConnection) -> IWallexRate:
        """Build the public feed with the shared native HTTP pool."""
        return WallexRateGateway(connection)

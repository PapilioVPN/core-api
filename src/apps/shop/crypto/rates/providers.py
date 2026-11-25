"""Bind the public market adapter and request-owned rate operations."""

from dishka import Provider, Scope, provide
from papilio.infra.http.connection import HTTPConnection

from .app.executions.refresh import RateRefreshExecution
from .app.interfaces.feed import IWallexRate
from .app.interfaces.refresh import IRateRefreshExecution
from .app.interfaces.services import IConversionService, ICryptoRateService
from .app.pipelines.refresh import RateRefreshPipeline
from .app.services.conversion import ConversionService
from .app.services.crud import CryptoRateService
from .infra.pg.repositories.crud import CryptoRateRepository
from .infra.wallex.client import WallexRateGateway


class CryptoRateProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(CryptoRateRepository)
    rates = provide(CryptoRateService, provides=ICryptoRateService)
    conversion = provide(
        ConversionService, scope=Scope.APP, provides=IConversionService
    )
    execution = provide(
        RateRefreshExecution, scope=Scope.APP, provides=IRateRefreshExecution
    )
    refresh = provide(RateRefreshPipeline, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def feed(self, connection: HTTPConnection) -> IWallexRate:
        """Build the public feed with the shared native HTTP pool."""
        return WallexRateGateway(connection)

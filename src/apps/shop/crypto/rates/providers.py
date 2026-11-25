"""Bind the shared market adapter, rate cache and conversion."""

from dishka import Provider, Scope, provide
from papilio.infra.http.connection import HTTPConnection

from .app.interfaces.cache import IRateCache
from .app.interfaces.feed import IWallexRate
from .app.interfaces.services import IConversionService
from .app.pipelines.refresh import RateRefreshPipeline
from .app.services.conversion import ConversionService
from .infra.redis.cache import RateCache
from .infra.wallex.client import WallexRateGateway


class CryptoRateProvider(Provider):
    scope = Scope.APP

    cache = provide(RateCache, provides=IRateCache)
    conversion = provide(ConversionService, provides=IConversionService)
    refresh = provide(RateRefreshPipeline)

    @provide
    def feed(self, connection: HTTPConnection) -> IWallexRate:
        """Build the public feed with the shared native HTTP pool."""
        return WallexRateGateway(connection)

"""Bind the shared market adapter, rate cache and conversion."""

from asyncio import timeout
from collections.abc import AsyncIterator
from importlib.util import find_spec

from dishka import Provider, Scope, provide
from nats.errors import Error as NatsError
from papilio.infra.http.connection import HTTPConnection

from src.settings.config import CoreSettings

from .app.interfaces.cache import IRateCache
from .app.interfaces.feed import IWallexRate
from .app.interfaces.refresh import IRateRefreshPublisher
from .app.interfaces.services import IConversionService
from .app.pipelines.refresh import RateRefreshPipeline
from .app.services.conversion import ConversionService
from .domain.results.records import RateFailure
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

    @provide
    async def publisher(
        self, settings: CoreSettings
    ) -> AsyncIterator[IRateRefreshPublisher | RateFailure]:
        """Open the optional jobs transport on the first manual refresh."""
        nats = settings.nats
        if (
            nats is None
            or settings.redis is None
            or not find_spec("taskiq_nats")
        ):
            yield RateFailure.QUEUE_UNAVAILABLE
        else:
            from src.shared.jobs import create_job_transport

            from .infra.broker.publishers import RateRefreshPublisher

            transport = create_job_transport(nats, settings.scheduler)
            try:
                try:
                    async with timeout(nats.connect_timeout):
                        await transport.startup()
                except (NatsError, OSError, TimeoutError):
                    yield RateFailure.QUEUE_UNAVAILABLE
                else:
                    yield RateRefreshPublisher(transport)
            finally:
                await transport.shutdown()

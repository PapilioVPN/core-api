"""Discover Xray's routing operations."""

from dishka import Provider, Scope, provide

from src.settings.config import CoreSettings
from src.shared.utils.asyncio.threads import ThreadRunner

from .app.executions.routing import XrayRoutingExecution
from .app.interfaces.operations import (
    IRoutingPayloadCodec,
    IXrayRoutingGateway,
    IXrayRoutingOperationRepository,
    IXrayRoutingOperations,
)
from .app.interfaces.reads import IXrayRoutingQuery, IXrayRoutingReader
from .app.pipelines.routing import XrayRoutingPipeline
from .app.queries.reads import XrayRoutingQuery
from .app.services.operations import XrayRoutingOperations
from .infra.crypto.payload import RoutingPayloadCodec
from .infra.grpc.mutations import XrayRoutingGateway
from .infra.grpc.reads import XrayRoutingReader
from .infra.pg.repositories.operations import XrayRoutingOperationRepository


class XrayRoutingProvider(Provider):
    scope = Scope.REQUEST

    query = provide(XrayRoutingQuery, provides=IXrayRoutingQuery)
    reader = provide(
        XrayRoutingReader, provides=IXrayRoutingReader, scope=Scope.APP
    )
    operations = provide(
        XrayRoutingOperations, provides=IXrayRoutingOperations
    )
    repository = provide(
        XrayRoutingOperationRepository,
        provides=IXrayRoutingOperationRepository,
    )
    gateway = provide(
        XrayRoutingGateway, provides=IXrayRoutingGateway, scope=Scope.APP
    )
    execution = provide(XrayRoutingExecution, scope=Scope.APP)
    pipeline = provide(XrayRoutingPipeline, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def payload(
        self, settings: CoreSettings, threads: ThreadRunner
    ) -> IRoutingPayloadCodec:
        """Use the configured deployment key in the existing thread runner."""
        return RoutingPayloadCodec(settings.crypto, threads)

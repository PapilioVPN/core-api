"""Bind the node registry and the application-owned host transport."""

from collections.abc import AsyncIterator
from contextlib import AsyncExitStack

from dishka import Provider, Scope, provide

from src.settings.config import CoreSettings

from .app.executions.probe import NodeProbeExecution
from .app.interfaces.endpoints import INodeEndpointQuery, INodeEndpointReader
from .app.interfaces.host import IHostStatsQuery, INodeHostGateway
from .app.interfaces.probe import INodeProbeRepository
from .app.interfaces.repositories import INodeRepository
from .app.interfaces.services import INodeService
from .app.pipelines.probe import NodeProbePipeline
from .app.queries.endpoints import NodeEndpointQuery
from .app.queries.host import HostStatsQuery
from .app.services.crud import NodeService
from .config import NodeHostConfig
from .infra.grpc.channels import NodeChannels
from .infra.grpc.host import NodeHostGateway
from .infra.pg.readers.endpoints import NodeEndpointReader
from .infra.pg.repositories.crud import NodeRepository
from .infra.pg.repositories.probe import NodeProbeRepository


class NodesProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(NodeRepository, provides=INodeRepository)
    nodes = provide(NodeService, provides=INodeService)
    endpoints = provide(NodeEndpointQuery, provides=INodeEndpointQuery)
    endpoint_reader = provide(NodeEndpointReader, provides=INodeEndpointReader)
    stats = provide(HostStatsQuery, provides=IHostStatsQuery)
    probe_repo = provide(NodeProbeRepository, provides=INodeProbeRepository)
    probe_execution = provide(NodeProbeExecution, scope=Scope.APP)
    probe = provide(NodeProbePipeline, scope=Scope.APP)
    host = provide(NodeHostGateway, provides=INodeHostGateway, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def host_config(self, settings: CoreSettings) -> NodeHostConfig:
        """Select the capability's deployment configuration."""
        return settings.node_host

    @provide(scope=Scope.APP)
    async def channels(
        self, config: NodeHostConfig
    ) -> AsyncIterator[NodeChannels]:
        """Provide one management channel owner for all Node RPC clients."""
        async with AsyncExitStack() as channels:
            yield NodeChannels(config, channels)

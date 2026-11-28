"""Bind application-owned Node channels and probe execution."""

from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide

from src.apps.network.nodes.registry.app.interfaces.credentials import (
    INodeCredentialCipher,
)

from .app.executions.probe import NodeProbeExecution
from .app.interfaces.probe import INodeProbeRepository
from .app.pipelines.probe import NodeProbePipeline
from .infra.grpc.channels import NodeChannels
from .infra.grpc.streams import NodeLogStreams
from .infra.pg.repositories.probe import NodeProbeRepository


class NodeConnectionsProvider(Provider):
    scope = Scope.APP

    probe_repo = provide(
        NodeProbeRepository, provides=INodeProbeRepository, scope=Scope.REQUEST
    )
    probe_execution = provide(NodeProbeExecution)
    probe = provide(NodeProbePipeline)
    log_streams = provide(NodeLogStreams)

    @provide
    async def channels(
        self, credentials: INodeCredentialCipher
    ) -> AsyncIterator[NodeChannels]:
        """Provide one management channel owner for all Node RPC clients."""
        channels = NodeChannels(credentials)
        try:
            yield channels
        finally:
            await channels.close()

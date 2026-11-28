"""Follow the pinned WireGuard log RPC on the shared Node channel."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from src.apps.network.nodes.connections.infra.grpc.streams import (
    NodeLogStreams,
)
from src.apps.network.nodes.observations.domain.results.logs import LogStream
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ...domain.results.logs import WireGuardLogEvent
from .codec import decode
from .v1.wireguard_diagnostics_pb2 import WireGuardDiagnosticsRequest
from .v1.wireguard_diagnostics_pb2_grpc import WireGuardDiagnosticsServiceStub


class WireGuardLogsGateway:
    def __init__(self, streams: NodeLogStreams) -> None:
        self.streams = streams

    @asynccontextmanager
    async def follow(
        self, node: NodeModel, name: str
    ) -> AsyncIterator[LogStream[WireGuardLogEvent]]:
        """Borrow one native log subscription for the Panel request.

        Args:
            node: Materialized Node registry record.
            name: Native WireGuard interface name.

        Yields:
            The bounded native feed or its typed admission outcome.
        """
        request = WireGuardDiagnosticsRequest(name=name)
        async with self.streams.follow(
            node.endpoint(),
            lambda channel, deadline: WireGuardDiagnosticsServiceStub(
                channel
            ).GetLogs(request, timeout=deadline),
            decode,
        ) as feed:
            yield feed

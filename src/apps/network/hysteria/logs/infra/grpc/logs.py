"""Follow the pinned Hysteria log RPC on the shared Node channel."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from src.apps.network.nodes.connections.infra.grpc.streams import (
    NodeLogStreams,
)
from src.apps.network.nodes.observations.domain.results.logs import LogStream
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ...domain.results.logs import HysteriaLogEvent
from .codec import decode
from .v1.hysteria_logs_pb2 import HysteriaLogsRequest
from .v1.hysteria_logs_pb2_grpc import HysteriaLogsServiceStub


class HysteriaLogsGateway:
    def __init__(self, streams: NodeLogStreams) -> None:
        self.streams = streams

    @asynccontextmanager
    async def follow(
        self, node: NodeModel, instance_id: str
    ) -> AsyncIterator[LogStream[HysteriaLogEvent]]:
        """Borrow one native log subscription for the Panel request.

        Args:
            node: Materialized Node registry record.
            instance_id: Native Hysteria instance identity.

        Yields:
            The bounded native feed or its typed admission outcome.
        """
        request = HysteriaLogsRequest(id=instance_id)
        async with self.streams.follow(
            node.endpoint(),
            lambda channel, deadline: HysteriaLogsServiceStub(channel).GetLogs(
                request, timeout=deadline
            ),
            decode,
        ) as feed:
            yield feed

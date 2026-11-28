"""Follow the pinned Xray log RPC on the shared Node channel."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from src.apps.network.nodes.connections.infra.grpc.streams import (
    NodeLogStreams,
)
from src.apps.network.nodes.observations.domain.results.logs import LogStream
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ...domain.results.live import XrayLogLine
from .codec import decode_line
from .v1 import logs_pb2 as wire
from .v1.logs_pb2_grpc import XrayLogsServiceStub


class XrayLogsGateway:
    def __init__(self, streams: NodeLogStreams) -> None:
        self.streams = streams

    @asynccontextmanager
    async def follow(
        self, node: NodeModel, instance_id: str
    ) -> AsyncIterator[LogStream[XrayLogLine]]:
        """Follow this execution and preserve its sequence gap information."""
        request = wire.XrayLogsRequest(id=instance_id)
        previous_sequence = None

        def decode(event: wire.XrayLogEvent) -> XrayLogLine:
            nonlocal previous_sequence
            line = decode_line(event, previous_sequence)
            previous_sequence = event.sequence
            return line

        async with self.streams.follow(
            node.endpoint(),
            lambda channel, deadline: XrayLogsServiceStub(channel).GetLogs(
                request, timeout=deadline
            ),
            decode,
        ) as feed:
            yield feed

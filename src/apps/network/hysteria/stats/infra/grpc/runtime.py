"""Read HysteriaRuntime through the pinned Node RPC."""

from src.apps.network.nodes.connections.infra.grpc.channels import NodeChannels
from src.apps.network.nodes.connections.infra.grpc.observation import observe
from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ...domain.results.runtime import HysteriaRuntime
from .v1.hysteria_stats_pb2 import HysteriaRuntimeStats, HysteriaStatsRequest
from .v1.hysteria_stats_pb2_grpc import HysteriaStatsServiceStub


def _decode(reply: HysteriaRuntimeStats) -> HysteriaRuntime | None:
    result = None
    if reply.execution > 0 and reply.ready_since_unix_nano > 0:
        result = HysteriaRuntime(
            execution=reply.execution,
            ready_since_unix_nanoseconds=reply.ready_since_unix_nano,
            uptime_seconds=reply.uptime_seconds,
        )
    return result


class HysteriaRuntimeGateway:
    def __init__(self, channels: NodeChannels) -> None:
        self.channels = channels

    async def read(
        self, node: NodeModel, instance_id: str
    ) -> NodeObservation[HysteriaRuntime]:
        """Send one bounded request over the shared authenticated channel."""
        result = await observe(
            self.channels,
            node,
            lambda channel: HysteriaStatsServiceStub(channel).GetRuntimeStats(
                HysteriaStatsRequest(id=instance_id),
                timeout=node.default_timeout,
            ),
            _decode,
        )
        return result

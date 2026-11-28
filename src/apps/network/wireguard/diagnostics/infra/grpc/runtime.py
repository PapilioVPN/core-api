"""Read WireGuardRuntime through the pinned Node RPC."""

from src.apps.network.nodes.connections.infra.grpc.channels import NodeChannels
from src.apps.network.nodes.connections.infra.grpc.observation import observe
from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ...domain.results.runtime import WireGuardRuntime
from .v1.wireguard_diagnostics_pb2 import (
    WireGuardDiagnosticsRequest,
    WireGuardRuntimeStats,
)
from .v1.wireguard_diagnostics_pb2_grpc import WireGuardDiagnosticsServiceStub


def _decode(reply: WireGuardRuntimeStats) -> WireGuardRuntime:
    return WireGuardRuntime(
        goroutines=reply.goroutines,
        gc_count=reply.gc_count,
        heap_bytes=reply.heap_bytes,
        allocated_bytes=reply.allocated_bytes,
        system_bytes=reply.system_bytes,
        allocations=reply.allocations,
        frees=reply.frees,
        live_objects=reply.live_objects,
        gc_pause_nanoseconds=reply.gc_pause_nanoseconds,
        uptime_seconds=reply.uptime_seconds
        if reply.HasField("uptime_seconds")
        else None,
    )


class WireGuardRuntimeGateway:
    def __init__(self, channels: NodeChannels) -> None:
        self.channels = channels

    async def read(
        self, node: NodeModel, name: str
    ) -> NodeObservation[WireGuardRuntime]:
        """Send one bounded request over the shared authenticated channel."""
        result = await observe(
            self.channels,
            node,
            lambda channel: WireGuardDiagnosticsServiceStub(
                channel
            ).GetRuntimeStats(
                WireGuardDiagnosticsRequest(name=name),
                timeout=node.default_timeout,
            ),
            _decode,
        )
        return result

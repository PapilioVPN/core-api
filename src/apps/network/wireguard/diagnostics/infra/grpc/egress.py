"""Read WireGuardEgress through the pinned Node RPC."""

from src.apps.network.nodes.connections.infra.grpc.channels import NodeChannels
from src.apps.network.nodes.connections.infra.grpc.observation import observe
from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ...domain.results.egress import WireGuardEgress
from .v1.wireguard_diagnostics_pb2 import (
    WireGuardDiagnosticsRequest,
    WireGuardEgressProbe,
)
from .v1.wireguard_diagnostics_pb2_grpc import WireGuardDiagnosticsServiceStub


def _decode(reply: WireGuardEgressProbe) -> WireGuardEgress | None:
    """Decode the probe result, including a confirmed unreachable target."""
    result = None
    if reply.HasField("observed_at") and reply.reachable == bool(
        reply.http_status
    ):
        try:
            observed_at = reply.observed_at.ToNanoseconds()
        except ValueError:
            pass
        else:
            result = WireGuardEgress(
                reachable=reply.reachable,
                http_status=reply.http_status or None,
                elapsed_nanoseconds=reply.elapsed_nanoseconds,
                observed_at_unix_nanoseconds=observed_at,
            )
    return result


class WireGuardEgressGateway:
    def __init__(self, channels: NodeChannels) -> None:
        self.channels = channels

    async def read(
        self, node: NodeModel, name: str
    ) -> NodeObservation[WireGuardEgress]:
        """Send one bounded request over the shared authenticated channel."""
        result = await observe(
            self.channels,
            node,
            lambda channel: WireGuardDiagnosticsServiceStub(
                channel
            ).ProbeEgress(
                WireGuardDiagnosticsRequest(name=name),
                timeout=node.default_timeout,
            ),
            _decode,
        )
        return result

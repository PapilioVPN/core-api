"""Read Xray counters over the authenticated Node channel."""

from src.apps.network.nodes.domain.models.records import NodeModel
from src.apps.network.nodes.domain.results.observation import NodeObservation
from src.apps.network.nodes.infra.grpc.channels import NodeChannels
from src.apps.network.nodes.infra.grpc.observation import observe

from ...domain.enums.traffic import XrayTrafficScope
from ...domain.results.traffic import XrayTraffic
from .codec import decode_counter, decode_traffic
from .v1.runtime_stats_pb2_grpc import XrayStatsServiceStub
from .v1.traffic_pb2 import XrayTrafficListRequest, XrayTrafficRequest
from .v1.traffic_pb2 import XrayTrafficScope as WireScope

_SCOPES = {
    XrayTrafficScope.INBOUND: WireScope.XRAY_TRAFFIC_SCOPE_INBOUND,
    XrayTrafficScope.OUTBOUND: WireScope.XRAY_TRAFFIC_SCOPE_OUTBOUND,
}


def encode_scope(scope: XrayTrafficScope) -> WireScope:
    """Translate the Network-owned counter selection to the wire enum."""
    return _SCOPES[scope]


class XrayTrafficGateway:
    def __init__(self, channels: NodeChannels) -> None:
        self.channels = channels

    async def get(
        self,
        node: NodeModel,
        instance_id: str,
        scope: XrayTrafficScope,
        name: str,
    ) -> NodeObservation[XrayTraffic]:
        """Read one exact counter pair over the selected Node channel.

        Args:
            node: Materialized registry endpoint.
            instance_id: Native instance identity.
            scope: Inbound or outbound counters.
            name: Exact inbound or outbound counter name.

        Returns:
            Native byte counters or a typed availability outcome.
        """
        result = await observe(
            self.channels,
            node,
            lambda channel: XrayStatsServiceStub(channel).GetTraffic(
                XrayTrafficRequest(
                    id=instance_id, scope=encode_scope(scope), name=name
                ),
                timeout=3,
            ),
            lambda reply: decode_counter(reply, name),
        )
        return result

    async def list(
        self, node: NodeModel, instance_id: str, scope: XrayTrafficScope
    ) -> NodeObservation[tuple[XrayTraffic, ...]]:
        """Read a bounded native snapshot over the selected Node channel.

        Args:
            node: Materialized registry endpoint.
            instance_id: Native instance identity.
            scope: Inbound or outbound counters.

        Returns:
            Native byte counters or a typed availability outcome.
        """
        result = await observe(
            self.channels,
            node,
            lambda channel: XrayStatsServiceStub(channel).ListTraffic(
                XrayTrafficListRequest(
                    id=instance_id, scope=encode_scope(scope)
                ),
                timeout=3,
            ),
            decode_traffic,
        )
        return result

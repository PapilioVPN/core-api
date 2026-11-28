"""Read outbound health over Xray's versioned Node contract."""

from src.apps.network.nodes.connections.infra.grpc.channels import NodeChannels
from src.apps.network.nodes.connections.infra.grpc.observation import observe
from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ...domain.results.health import XrayOutboundSample
from .codec import decode_health
from .v1.outbounds_pb2 import XrayOutboundHealthRequest
from .v1.outbounds_pb2_grpc import XrayOutboundsServiceStub


class XrayOutboundHealthGateway:
    def __init__(self, channels: NodeChannels) -> None:
        self.channels = channels

    async def read(
        self, node: NodeModel, instance_id: str, tag: str | None
    ) -> NodeObservation[tuple[XrayOutboundSample, ...]]:
        """Issue one bounded read on the selected Node channel.

        Args:
            node: Materialized registry endpoint.
            instance_id: Native instance identity.
            tag: Optional exact outbound tag.

        Returns:
            A typed snapshot or an availability outcome.
        """
        result = await observe(
            self.channels,
            node,
            lambda channel: XrayOutboundsServiceStub(
                channel
            ).GetOutboundHealth(
                XrayOutboundHealthRequest(id=instance_id, tag=tag), timeout=2
            ),
            lambda reply: decode_health(reply, tag),
        )
        return result

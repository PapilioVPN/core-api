"""Call the versioned WireGuard GetStatus RPC."""

from src.apps.network.nodes.connections.infra.grpc.channels import NodeChannels
from src.apps.network.nodes.connections.infra.grpc.observation import observe
from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ...domain.results.status import WireGuardStatus
from .codec import decode
from .v1.interfaces_pb2 import WireGuardInterfaceRequest
from .v1.interfaces_pb2_grpc import WireGuardInterfacesServiceStub


class WireGuardStatusGateway:
    def __init__(self, channels: NodeChannels) -> None:
        self.channels = channels

    async def read(
        self, node: NodeModel, target_name: str
    ) -> NodeObservation[WireGuardStatus]:
        """Call once using the registered TLS target and a bounded deadline.

        Args:
            node: Registered endpoint selected by the owning operation.
            target_name: Native WireGuard target identity.

        Returns:
            A typed reply or an availability status without raw diagnostics.
        """
        result = await observe(
            self.channels,
            node,
            lambda channel: WireGuardInterfacesServiceStub(channel).GetStatus(
                WireGuardInterfaceRequest(name=target_name), timeout=3
            ),
            lambda reply: decode(reply, target_name),
        )
        return result

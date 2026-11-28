"""Read WireGuard peers over the published Node v1 contract."""

from base64 import b64encode

from src.apps.network.nodes.connections.infra.grpc.channels import NodeChannels
from src.apps.network.nodes.connections.infra.grpc.observation import observe
from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ....interfaces.infra.grpc.v1.interfaces_pb2 import (
    WireGuardInterfaceRequest,
    WireGuardPeerMembership,
)
from ....interfaces.infra.grpc.v1.interfaces_pb2_grpc import (
    WireGuardInterfacesServiceStub,
)
from ...domain.results.membership import WireGuardPeer


def _decode(
    reply: WireGuardPeerMembership,
) -> tuple[WireGuardPeer, ...] | None:
    keys = {peer.public_key for peer in reply.peers}
    result = None
    if len(keys) == len(reply.peers) and all(len(key) == 32 for key in keys):
        result = tuple(
            WireGuardPeer(
                b64encode(peer.public_key).decode("ascii"),
                tuple(peer.allowed_ips),
            )
            for peer in reply.peers
        )
    return result


class WireGuardMembershipGateway:
    def __init__(self, channels: NodeChannels) -> None:
        self.channels = channels

    async def read(
        self, node: NodeModel, name: str
    ) -> NodeObservation[tuple[WireGuardPeer, ...]]:
        """Call ListPeers once on the shared authenticated channel.

        Args:
            node: Registered management target.
            name: Native WireGuard interface name.

        Returns:
            Public peer metadata from Node or its typed delivery outcome.
        """
        result = await observe(
            self.channels,
            node,
            lambda channel: WireGuardInterfacesServiceStub(channel).ListPeers(
                WireGuardInterfaceRequest(name=name), timeout=3
            ),
            _decode,
        )
        return result

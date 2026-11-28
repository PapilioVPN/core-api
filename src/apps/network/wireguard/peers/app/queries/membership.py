"""Observe the live peers of a registered WireGuard interface."""

from src.apps.network.nodes.observations.domain.enums.observation import (
    NodeReadStatus,
)
from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.app.interfaces.services import (
    INodeService,
)

from ...domain.results.membership import WireGuardPeer
from ..interfaces.membership import IWireGuardMembershipGateway


class WireGuardMembershipQuery:
    def __init__(
        self, nodes: INodeService, gateway: IWireGuardMembershipGateway
    ) -> None:
        self.nodes = nodes
        self.gateway = gateway

    async def get(
        self, node_id: int, name: str
    ) -> NodeObservation[tuple[WireGuardPeer, ...]]:
        """Read effective membership of an enabled registered target.

        Args:
            node_id: Core registry identity.
            name: Native WireGuard interface name.

        Returns:
            A live observation, including an empty membership, or a status.

        Raises:
            NotFoundException: The Node is absent from the registry.
        """
        node = await self.nodes.get_by_id(node_id)
        if node.is_enabled:
            result = await self.gateway.read(node, name)
        else:
            result = NodeObservation[tuple[WireGuardPeer, ...]](
                NodeReadStatus.DISABLED
            )
        return result

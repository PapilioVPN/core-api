"""Use the selected enabled registry entry for WireGuard status."""

from src.apps.network.nodes.app.interfaces.services import INodeService
from src.apps.network.nodes.domain.enums.observation import NodeReadStatus
from src.apps.network.nodes.domain.results.observation import NodeObservation

from ...domain.results.status import WireGuardStatus
from ..interfaces.status import IWireGuardStatusGateway


class WireGuardStatusQuery:
    def __init__(
        self, nodes: INodeService, gateway: IWireGuardStatusGateway
    ) -> None:
        self.nodes = nodes
        self.gateway = gateway

    async def get(
        self, node_id: int, target_name: str
    ) -> NodeObservation[WireGuardStatus]:
        """Read live status for one registered Node.

        Args:
            node_id: Stable Node registry identity.
            target_name: Native WireGuard target identity.

        Returns:
            The typed observation or its availability status.

        Raises:
            NotFoundException: The Node is absent from the registry.
        """
        node = await self.nodes.get_by_id(node_id)
        if node.is_enabled:
            result = await self.gateway.read(node, target_name)
        else:
            result = NodeObservation[WireGuardStatus](NodeReadStatus.DISABLED)
        return result

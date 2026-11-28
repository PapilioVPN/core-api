"""Use the selected enabled registry entry for OpenVPN status."""

from src.apps.network.nodes.app.interfaces.services import INodeService
from src.apps.network.nodes.domain.enums.observation import NodeReadStatus
from src.apps.network.nodes.domain.results.observation import NodeObservation

from ...domain.results.status import OpenVPNStatus
from ..interfaces.status import IOpenVPNStatusGateway


class OpenVPNStatusQuery:
    def __init__(
        self, nodes: INodeService, gateway: IOpenVPNStatusGateway
    ) -> None:
        self.nodes = nodes
        self.gateway = gateway

    async def get(
        self, node_id: int, instance_id: str
    ) -> NodeObservation[OpenVPNStatus]:
        """Read live status for one registered Node.

        Args:
            node_id: Stable Node registry identity.
            instance_id: Native OpenVPN target identity.

        Returns:
            The typed observation or its availability status.

        Raises:
            NotFoundException: The Node is absent from the registry.
        """
        node = await self.nodes.get_by_id(node_id)
        if node.is_enabled:
            result = await self.gateway.read(node, instance_id)
        else:
            result = NodeObservation[OpenVPNStatus](NodeReadStatus.DISABLED)
        return result

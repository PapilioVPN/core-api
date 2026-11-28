"""Use the selected enabled registry entry for Hysteria status."""

from src.apps.network.nodes.observations.domain.enums.observation import (
    NodeReadStatus,
)
from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.app.interfaces.services import (
    INodeService,
)

from ...domain.results.status import HysteriaStatus
from ..interfaces.status import IHysteriaStatusGateway


class HysteriaStatusQuery:
    def __init__(
        self, nodes: INodeService, gateway: IHysteriaStatusGateway
    ) -> None:
        self.nodes = nodes
        self.gateway = gateway

    async def get(
        self, node_id: int, instance_id: str
    ) -> NodeObservation[HysteriaStatus]:
        """Read live status for one registered Node.

        Args:
            node_id: Stable Node registry identity.
            instance_id: Native Hysteria target identity.

        Returns:
            The typed observation or its availability status.

        Raises:
            NotFoundException: The Node is absent from the registry.
        """
        node = await self.nodes.get_by_id(node_id)
        if node.is_enabled:
            result = await self.gateway.read(node, instance_id)
        else:
            result = NodeObservation[HysteriaStatus](NodeReadStatus.DISABLED)
        return result

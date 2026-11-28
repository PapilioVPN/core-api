"""Select an enabled Node before reading runtime VLESS membership."""

from src.apps.network.nodes.observations.domain.enums.observation import (
    NodeReadStatus,
)
from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.app.interfaces.services import (
    INodeService,
)

from ..interfaces.count import IXrayVlessCountGateway


class XrayVlessCountQuery:
    def __init__(
        self, nodes: INodeService, gateway: IXrayVlessCountGateway
    ) -> None:
        self.nodes = nodes
        self.gateway = gateway

    async def get(
        self, node_id: int, instance_id: str, inbound_tag: str
    ) -> NodeObservation[int]:
        """Observe one exact inbound without returning subscriber identity."""
        node = await self.nodes.get_by_id(node_id)
        if node.is_enabled:
            result = await self.gateway.get(node, instance_id, inbound_tag)
        else:
            result = NodeObservation[int](NodeReadStatus.DISABLED)
        return result

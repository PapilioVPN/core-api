"""Read Xray outbound health from a selected registered Node."""

from src.apps.network.nodes.app.interfaces.services import INodeService
from src.apps.network.nodes.domain.enums.observation import NodeReadStatus
from src.apps.network.nodes.domain.results.observation import NodeObservation

from ...domain.results.health import XrayOutboundSample
from ..interfaces.health import IXrayOutboundHealthGateway


class XrayOutboundHealthQuery:
    def __init__(
        self, nodes: INodeService, gateway: IXrayOutboundHealthGateway
    ) -> None:
        self.nodes = nodes
        self.gateway = gateway

    async def get(
        self, node_id: int, instance_id: str, tag: str | None
    ) -> NodeObservation[tuple[XrayOutboundSample, ...]]:
        """Observe outbound health on one enabled Node.

        Args:
            node_id: Stable Node registry identity.
            instance_id: Native instance identity.
            tag: Optional exact outbound tag.

        Returns:
            The live view or a typed availability outcome.

        Raises:
            NotFoundException: The Node is absent from the registry.
        """
        node = await self.nodes.get_by_id(node_id)
        if node.is_enabled:
            result = await self.gateway.read(node, instance_id, tag)
        else:
            result = NodeObservation[tuple[XrayOutboundSample, ...]](
                NodeReadStatus.DISABLED
            )
        return result

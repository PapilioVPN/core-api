"""Read the selected registered node's observed Xray state."""

from src.apps.network.nodes.registry.app.interfaces.services import (
    INodeService,
)
from src.apps.network.nodes.registry.domain.results.records import NodeEndpoint

from ...domain.enums.status import XrayStatusCode
from ...domain.results.status import XrayStatusResult
from ..interfaces.status import IXrayStatusGateway


class XrayStatusQuery:
    def __init__(
        self, nodes: INodeService, gateway: IXrayStatusGateway
    ) -> None:
        """Bind the registry and the Xray status transport."""
        self.nodes = nodes
        self.gateway = gateway

    async def get(self, node_id: int, instance_id: str) -> XrayStatusResult:
        """Observe one enabled node without writing or reading revisions.

        Args:
            node_id: Stable Core registry ID.
            instance_id: Native Xray instance ID on the node.

        Returns:
            A live observation or the reason a read was not possible.

        Raises:
            NotFoundException: The node is not registered.
        """
        node = await self.nodes.get_by_id(node_id)
        result = await self.observe_target(node.endpoint(), instance_id)
        return result

    async def observe_target(
        self, node: NodeEndpoint, instance_id: str
    ) -> XrayStatusResult:
        """Observe the exact registry snapshot without another SQL read."""
        if node.is_enabled:
            result = await self.gateway.read(node, instance_id)
        else:
            result = XrayStatusResult(XrayStatusCode.DISABLED)
        return result

"""Read Xray runtime metrics from a selected registered Node."""

from src.apps.network.nodes.observations.domain.enums.observation import (
    NodeReadStatus,
)
from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.app.interfaces.services import (
    INodeService,
)

from ...domain.results.runtime import XrayRuntime
from ..interfaces.runtime import IXrayRuntimeGateway


class XrayRuntimeQuery:
    def __init__(
        self, nodes: INodeService, gateway: IXrayRuntimeGateway
    ) -> None:
        self.nodes = nodes
        self.gateway = gateway

    async def get(
        self, node_id: int, instance_id: str
    ) -> NodeObservation[XrayRuntime]:
        """Observe runtime metrics on one enabled Node.

        Args:
            node_id: Stable Node registry identity.
            instance_id: Native instance identity.

        Returns:
            The live view or a typed availability outcome.

        Raises:
            NotFoundException: The Node is absent from the registry.
        """
        node = await self.nodes.get_by_id(node_id)
        if node.is_enabled:
            result = await self.gateway.read(node, instance_id)
        else:
            result = NodeObservation[XrayRuntime](NodeReadStatus.DISABLED)
        return result

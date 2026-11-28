"""Observe HysteriaRuntime on one registered node."""

from src.apps.network.nodes.observations.domain.enums.observation import (
    NodeReadStatus,
)
from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.app.interfaces.services import (
    INodeService,
)

from ...domain.results.runtime import HysteriaRuntime
from ..interfaces.runtime import IHysteriaRuntimeGateway


class HysteriaRuntimeQuery:
    def __init__(
        self, nodes: INodeService, gateway: IHysteriaRuntimeGateway
    ) -> None:
        self.nodes = nodes
        self.gateway = gateway

    async def get(
        self, node_id: int, instance_id: str
    ) -> NodeObservation[HysteriaRuntime]:
        """Resolve the node before the live RPC and honor its enabled state."""
        node = await self.nodes.get_by_id(node_id)
        if node.is_enabled:
            result = await self.gateway.read(node, instance_id)
        else:
            result = NodeObservation[HysteriaRuntime](NodeReadStatus.DISABLED)
        return result

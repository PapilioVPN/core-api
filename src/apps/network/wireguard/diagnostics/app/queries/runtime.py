"""Observe WireGuardRuntime on one registered node."""

from src.apps.network.nodes.observations.domain.enums.observation import (
    NodeReadStatus,
)
from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.app.interfaces.services import (
    INodeService,
)

from ...domain.results.runtime import WireGuardRuntime
from ..interfaces.runtime import IWireGuardRuntimeGateway


class WireGuardRuntimeQuery:
    def __init__(
        self, nodes: INodeService, gateway: IWireGuardRuntimeGateway
    ) -> None:
        self.nodes = nodes
        self.gateway = gateway

    async def get(
        self, node_id: int, name: str
    ) -> NodeObservation[WireGuardRuntime]:
        """Resolve the node before the live RPC and honor its enabled state."""
        node = await self.nodes.get_by_id(node_id)
        if node.is_enabled:
            result = await self.gateway.read(node, name)
        else:
            result = NodeObservation[WireGuardRuntime](NodeReadStatus.DISABLED)
        return result

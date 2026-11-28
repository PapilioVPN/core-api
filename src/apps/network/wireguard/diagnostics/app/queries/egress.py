"""Observe WireGuardEgress on one registered node."""

from src.apps.network.nodes.observations.domain.enums.observation import (
    NodeReadStatus,
)
from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.app.interfaces.services import (
    INodeService,
)

from ...domain.results.egress import WireGuardEgress
from ..interfaces.egress import IWireGuardEgressGateway


class WireGuardEgressQuery:
    def __init__(
        self, nodes: INodeService, gateway: IWireGuardEgressGateway
    ) -> None:
        self.nodes = nodes
        self.gateway = gateway

    async def get(
        self, node_id: int, name: str
    ) -> NodeObservation[WireGuardEgress]:
        """Resolve the node before the live RPC and honor its enabled state."""
        node = await self.nodes.get_by_id(node_id)
        if node.is_enabled:
            result = await self.gateway.read(node, name)
        else:
            result = NodeObservation[WireGuardEgress](NodeReadStatus.DISABLED)
        return result

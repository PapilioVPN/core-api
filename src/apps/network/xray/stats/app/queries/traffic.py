"""Observe Xray counters on a selected registered Node."""

from src.apps.network.nodes.observations.domain.enums.observation import (
    NodeReadStatus,
)
from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.app.interfaces.services import (
    INodeService,
)

from ...domain.enums.traffic import XrayTrafficScope
from ...domain.results.traffic import XrayTraffic
from ..interfaces.traffic import IXrayTrafficGateway


class XrayTrafficQuery:
    def __init__(
        self, nodes: INodeService, gateway: IXrayTrafficGateway
    ) -> None:
        self.nodes = nodes
        self.gateway = gateway

    async def get(
        self,
        node_id: int,
        instance_id: str,
        scope: XrayTrafficScope,
        name: str,
    ) -> NodeObservation[XrayTraffic]:
        """Observe one exact counter pair for one scope.

        Args:
            node_id: Stable Node registry identity.
            instance_id: Native instance identity.
            scope: Inbound or outbound counters.
            name: Exact inbound or outbound counter name.

        Returns:
            Live traffic counters in bytes or a typed availability outcome.

        Raises:
            NotFoundException: The Node is absent from the registry.
        """
        node = await self.nodes.get_by_id(node_id)
        if node.is_enabled:
            result = await self.gateway.get(node, instance_id, scope, name)
        else:
            result = NodeObservation[XrayTraffic](NodeReadStatus.DISABLED)
        return result

    async def list(
        self, node_id: int, instance_id: str, scope: XrayTrafficScope
    ) -> NodeObservation[tuple[XrayTraffic, ...]]:
        """Observe a bounded native snapshot for one scope.

        Args:
            node_id: Stable Node registry identity.
            instance_id: Native instance identity.
            scope: Inbound or outbound counters.

        Returns:
            Live traffic counters in bytes or a typed availability outcome.

        Raises:
            NotFoundException: The Node is absent from the registry.
        """
        node = await self.nodes.get_by_id(node_id)
        if node.is_enabled:
            result = await self.gateway.list(node, instance_id, scope)
        else:
            result = NodeObservation[tuple[XrayTraffic, ...]](
                NodeReadStatus.DISABLED
            )
        return result

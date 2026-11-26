"""Coordinate one live read of an enabled registered node."""

from ...domain.enums.host import HostStatsStatus
from ...domain.results.host import HostStatsResult
from ..interfaces.host import INodeHostGateway
from ..interfaces.services import INodeService


class HostStatsQuery:
    def __init__(self, nodes: INodeService, gateway: INodeHostGateway) -> None:
        self.nodes = nodes
        self.gateway = gateway

    async def get(self, node_id: int) -> HostStatsResult:
        """Read one authorized node's current host observations.

        Args:
            node_id: Stable ID of the registered node.

        Returns:
            The live snapshot or the reason no snapshot was obtained.

        Raises:
            NotFoundException: The node is absent from the registry.
        """
        node = await self.nodes.get_by_id(node_id)
        if node.is_enabled:
            result = await self.gateway.read(node_id, node.address, node.port)
        else:
            result = HostStatsResult(HostStatsStatus.DISABLED)
        return result

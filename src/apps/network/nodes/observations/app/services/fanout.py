"""Bound simultaneous fleet observations for this API process."""

from anyio import CapacityLimiter, WouldBlock

from src.apps.network.nodes.registry.domain.results.records import NodeEndpoint

from ...domain.enums.host import HostStatsStatus
from ...domain.results.host import HostStatsResult
from ..interfaces.host import INodeHostGateway

_MAX_IN_FLIGHT = 32


class HostStatsFanout:
    def __init__(self, gateway: INodeHostGateway) -> None:
        self.gateway = gateway
        self.capacity = CapacityLimiter(_MAX_IN_FLIGHT)

    async def read(self, node: NodeEndpoint) -> HostStatsResult:
        """Run one read or report saturation immediately.

        Args:
            node: The selected enabled management target.

        Returns:
            The live outcome or a busy result when capacity is exhausted.
        """
        try:
            self.capacity.acquire_nowait()
        except WouldBlock:
            result = HostStatsResult(HostStatsStatus.BUSY)
        else:
            try:
                result = await self.gateway.read(node)
            finally:
                self.capacity.release()
        return result

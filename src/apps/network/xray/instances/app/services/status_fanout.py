"""Cap fleet reads across requests without queuing new remote calls."""

from anyio import CapacityLimiter, WouldBlock

from src.apps.network.nodes.registry.domain.results.records import NodeEndpoint

from ...domain.enums.status import XrayStatusCode
from ...domain.results.status import XrayStatusResult
from ..interfaces.status import IXrayStatusGateway

_MAX_IN_FLIGHT = 32


class XrayStatusFanout:
    def __init__(self, gateway: IXrayStatusGateway) -> None:
        self.gateway = gateway
        self.capacity = CapacityLimiter(_MAX_IN_FLIGHT)

    async def read(
        self, endpoint: NodeEndpoint, instance_id: str
    ) -> XrayStatusResult:
        """Issue one bounded read or report local saturation immediately."""
        try:
            self.capacity.acquire_nowait()
        except WouldBlock:
            result = XrayStatusResult(XrayStatusCode.BUSY)
        else:
            try:
                result = await self.gateway.read(endpoint, instance_id)
            finally:
                self.capacity.release()
        return result

"""Select an enabled Node for WireGuard logs."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from src.apps.network.nodes.observations.domain.enums.logs import LogStreamEnd
from src.apps.network.nodes.observations.domain.results.logs import LogStream
from src.apps.network.nodes.registry.app.interfaces.services import (
    INodeService,
)

from ...domain.results.logs import WireGuardLogEvent
from ..interfaces.logs import IWireGuardLogsGateway


class WireGuardLogsQuery:
    def __init__(
        self, nodes: INodeService, gateway: IWireGuardLogsGateway
    ) -> None:
        self.nodes = nodes
        self.gateway = gateway

    @asynccontextmanager
    async def follow(
        self, node_id: int, name: str
    ) -> AsyncIterator[LogStream[WireGuardLogEvent]]:
        """Select one registered Node and borrow its log subscription.

        Args:
            node_id: Core registry identity.
            name: Native WireGuard interface name.

        Yields:
            The live feed or its typed admission outcome.

        Raises:
            NotFoundException: The Node is absent from the registry.
        """
        node = await self.nodes.get_by_id(node_id)
        if node.is_enabled:
            async with self.gateway.follow(node, name) as feed:
                yield feed
        else:
            yield LogStream(end=LogStreamEnd.DISABLED)

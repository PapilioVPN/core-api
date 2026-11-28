"""Select the authorized Node registry target before opening the live feed."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from src.apps.network.nodes.observations.domain.enums.logs import LogStreamEnd
from src.apps.network.nodes.observations.domain.results.logs import LogStream
from src.apps.network.nodes.registry.app.interfaces.services import (
    INodeService,
)

from ...domain.results.live import XrayLogLine
from ..interfaces.live import IXrayLogsGateway


class XrayLogsQuery:
    def __init__(self, nodes: INodeService, gateway: IXrayLogsGateway) -> None:
        self.nodes = nodes
        self.gateway = gateway

    @asynccontextmanager
    async def follow(
        self, node_id: int, instance_id: str
    ) -> AsyncIterator[LogStream[XrayLogLine]]:
        """Read the registry once and borrow the chosen log subscription.

        Args:
            node_id: Stable registered Node identity.
            instance_id: Native Xray instance identity.

        Yields:
            An active log feed or its typed admission outcome.

        Raises:
            NotFoundException: The Node is absent from the registry.
        """
        node = await self.nodes.get_by_id(node_id)
        if node.is_enabled:
            async with self.gateway.follow(node, instance_id) as feed:
                yield feed
        else:
            yield LogStream(end=LogStreamEnd.DISABLED)

"""Select an enabled Node for OpenVPN logs."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from src.apps.network.nodes.observations.domain.enums.logs import LogStreamEnd
from src.apps.network.nodes.observations.domain.results.logs import LogStream
from src.apps.network.nodes.registry.app.interfaces.services import (
    INodeService,
)

from ...domain.dtos.logs import OpenVPNLogInput
from ...domain.results.logs import OpenVPNLogBatch
from ..interfaces.logs import IOpenVPNLogsGateway


class OpenVPNLogsQuery:
    def __init__(
        self, nodes: INodeService, gateway: IOpenVPNLogsGateway
    ) -> None:
        self.nodes = nodes
        self.gateway = gateway

    @asynccontextmanager
    async def follow(
        self, node_id: int, instance_id: str, selection: OpenVPNLogInput
    ) -> AsyncIterator[LogStream[OpenVPNLogBatch]]:
        """Select one registered Node and borrow its log subscription.

        Args:
            node_id: Core registry identity.
            instance_id: Native OpenVPN instance identity.
            selection: Optional execution identity and resume cursor.

        Yields:
            The live feed or its typed admission outcome.

        Raises:
            NotFoundException: The Node is absent from the registry.
        """
        node = await self.nodes.get_by_id(node_id)
        if node.is_enabled:
            async with self.gateway.follow(
                node, instance_id, selection
            ) as feed:
                yield feed
        else:
            yield LogStream(end=LogStreamEnd.DISABLED)

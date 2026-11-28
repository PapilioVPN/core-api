"""Capture desired metadata and a registered endpoint in a short SQL scope."""

from papilio.infra.db.tools.decorators import transactional

from src.apps.network.nodes.registry.app.interfaces.endpoints import (
    INodeEndpointQuery,
)

from ...domain.results.records import XrayAssignmentSelection
from ..interfaces.records import IXrayAssignmentReader


class XrayAssignmentQuery:
    def __init__(
        self,
        nodes: INodeEndpointQuery,
        assignments: IXrayAssignmentReader,
    ) -> None:
        self.nodes = nodes
        self.assignments = assignments

    @transactional
    async def get(
        self, node_id: int, instance_id: str
    ) -> XrayAssignmentSelection:
        """Finish SQL before the target can be used by the Node query."""
        node = await self.nodes.get_endpoint(node_id)
        desired = await self.assignments.select_one(node_id, instance_id)
        return XrayAssignmentSelection(node, desired)

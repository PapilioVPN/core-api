"""Return selected registry endpoints before any external network waits."""

from papilio.infra.db.tools.decorators import transactional
from papilio.tools.checks import IDChecks

from ...domain.results.records import NodeEndpoint
from ..interfaces.endpoints import INodeEndpointReader


class NodeEndpointQuery(IDChecks[NodeEndpoint]):
    entity = "Node"

    def __init__(self, reader: INodeEndpointReader) -> None:
        self.reader = reader

    @transactional
    async def get_endpoint(self, id: int) -> NodeEndpoint:
        """Read one registered endpoint or raise the Node not-found error."""
        endpoint = await self.reader.select_endpoint(id)
        return self._check_for_id_existence(id, endpoint)

    @transactional
    async def get_endpoints(
        self, ids: tuple[int, ...]
    ) -> dict[int, NodeEndpoint]:
        """Read selected endpoints, omitting absent registry IDs."""
        endpoints = await self.reader.select_endpoints(ids) if ids else {}
        return endpoints

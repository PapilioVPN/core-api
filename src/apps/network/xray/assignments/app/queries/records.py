"""Capture desired metadata and a registered endpoint in a short SQL scope."""

from papilio.infra.db.tools.decorators import transactional

from src.apps.network.nodes.app.interfaces.endpoints import INodeEndpointQuery
from src.apps.network.xray.revisions.app.interfaces.records import (
    IXrayRevisionService,
)

from ...domain.results.records import (
    XrayAssignmentSelection,
    XrayDesiredRevision,
)
from ..interfaces.records import IXrayAssignmentRepository


class XrayAssignmentQuery:
    def __init__(
        self,
        nodes: INodeEndpointQuery,
        revisions: IXrayRevisionService,
        repo: IXrayAssignmentRepository,
    ) -> None:
        self.nodes = nodes
        self.revisions = revisions
        self.repo = repo

    @transactional
    async def get(
        self, node_id: int, instance_id: str
    ) -> XrayAssignmentSelection:
        """Finish SQL before the target can be used by the Node query."""
        node = await self.nodes.get_endpoint(node_id)
        assignment = await self.repo.find(node_id, instance_id)
        desired = None
        if assignment is not None:
            revision = await self.revisions.get_by_id(assignment.revision_id)
            desired = XrayDesiredRevision(
                revision.id, revision.config_sha256, assignment.updated_at
            )
        return XrayAssignmentSelection(node, desired)

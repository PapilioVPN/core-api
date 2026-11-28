"""Change desired revision only. Applying it is a separate operation."""

from papilio.infra.db.tools.decorators import transactional

from src.apps.network.nodes.registry.app.interfaces.services import (
    INodeService,
)
from src.apps.network.xray.revisions.app.interfaces.records import (
    IXrayRevisionService,
)

from ...domain.results.records import XrayDesiredRevision
from ..interfaces.records import IXrayAssignmentRepository


class XrayAssignmentService:
    def __init__(
        self,
        nodes: INodeService,
        revisions: IXrayRevisionService,
        repo: IXrayAssignmentRepository,
    ) -> None:
        self.nodes = nodes
        self.revisions = revisions
        self.repo = repo

    @transactional
    async def set(
        self, node_id: int, instance_id: str, revision_id: int
    ) -> XrayDesiredRevision:
        """Point this registered instance at one immutable saved revision."""
        await self.nodes.get_by_id(node_id)
        revision = await self.revisions.lock_for_reference(revision_id)
        record = await self.repo.set_revision(
            node_id, instance_id, revision.id
        )
        return XrayDesiredRevision(
            record.revision_id, revision.config_sha256, record.updated_at
        )

    @transactional
    async def clear(self, node_id: int, instance_id: str) -> None:
        """Remove the desired link without touching active execution."""
        await self.nodes.get_by_id(node_id)
        await self.repo.clear(node_id, instance_id)

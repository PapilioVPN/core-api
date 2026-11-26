"""Manage node records without contacting remote servers."""

from papilio.infra.db.tools.conflicts import handle_conflicts
from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks

from ...domain.dtos.records import NodeCreate, NodeList, NodeUpdate
from ...domain.models.records import NodeModel
from ..interfaces.repositories import INodeRepository


class NodeService(IDChecks[NodeModel]):
    entity = "Node"

    def __init__(self, repo: INodeRepository) -> None:
        """Bind the request's node repository."""
        self.repo = repo

    @handle_conflicts(entity="Node")
    @transactional
    async def create(self, data: NodeCreate) -> NodeModel:
        """Register a managed node.

        Args:
            data: Validated name, management endpoint and operator state.

        Returns:
            The independently stored node.

        Raises:
            ConflictException: The management endpoint is already registered.
        """
        node = await self.repo.create(
            NodeModel(
                name=data.name,
                address=data.address,
                port=data.port,
                is_enabled=data.is_enabled,
            )
        )
        return node

    @transactional
    async def get_by_id(self, id: int) -> NodeModel:
        """Read the stored registry record.

        Args:
            id: Stable Core node identity.

        Returns:
            The matching node, materialized before any caller's remote I/O.

        Raises:
            NotFoundException: The node is absent.
        """
        node = await self.repo.get_by_id(id)
        return self._check_for_id_existence(id, node)

    async def list(self, query: NodeList) -> PagedType[NodeModel]:
        """Read an operator's filtered registry page.

        Args:
            query: Validated paging, search and operator state filters.

        Returns:
            Nodes newest by identity first, with the filtered count.
        """
        page = await self.repo.list(
            limit=query.per_page,
            offset=(query.page - 1) * query.per_page,
            q=query.q,
            is_enabled=query.is_enabled,
        )
        return page

    @handle_conflicts(entity="Node")
    @transactional
    async def update(self, id: int, data: NodeUpdate) -> NodeModel:
        """Update selected registry fields without changing the node identity.

        Args:
            id: Stable Core node identity.
            data: Changes, excluding fields the operator omitted.

        Returns:
            The updated stored node.

        Raises:
            ValidationException: No recognized field was supplied.
            NotFoundException: The node is absent.
            ConflictException: A different node uses the resulting endpoint.
        """
        changes = self._check_not_empty_dict(data.to_row())
        node = await self.repo.update_by_id(id, changes)
        return self._check_for_id_existence(id, node)

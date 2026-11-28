"""Manage node records without contacting remote servers."""

from papilio.errors.exceptions import ValidationException
from papilio.infra.db.tools.conflicts import handle_conflicts
from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks
from pydantic import SecretStr

from src.shared.utils.order import changed_positions

from ...domain.dtos.records import (
    NodeCreate,
    NodeList,
    NodeOrderInput,
    NodeUpdate,
)
from ...domain.models.records import NodeModel
from ..interfaces.credentials import INodeCredentialCipher
from ..interfaces.repositories import INodeRepository


class NodeService(IDChecks[NodeModel]):
    entity = "Node"

    def __init__(
        self, repo: INodeRepository, credentials: INodeCredentialCipher
    ) -> None:
        """Bind registry persistence and storage encryption."""
        self.repo = repo
        self.credentials = credentials

    async def create(self, data: NodeCreate) -> NodeModel:
        """Register a managed node.

        Args:
            data: Validated name, management endpoint and operator state.

        Returns:
            The independently stored node.

        Raises:
            ConflictException: The management endpoint is already registered.
        """
        ciphertext = await self._seal(data.api_key)
        node = await self._create(
            NodeModel(
                name=data.name,
                address=data.address,
                port=data.port,
                default_timeout=data.default_timeout,
                is_enabled=data.is_enabled,
                api_key_ciphertext=ciphertext,
                ca_pem=data.ca_pem,
            )
        )
        return node

    @handle_conflicts(entity="Node")
    @transactional
    async def _create(self, data: NodeModel) -> NodeModel:
        node = await self.repo.create(data)
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
            Nodes in display order, with the filtered count.
        """
        page = await self.repo.list(
            limit=query.per_page,
            offset=(query.page - 1) * query.per_page,
            q=query.q,
            is_enabled=query.is_enabled,
        )
        return page

    @transactional
    async def reorder(self, data: NodeOrderInput) -> None:
        """Reassign the selected nodes' existing display positions.

        Args:
            data: Distinct node IDs in the operator's requested order.

        Raises:
            NotFoundException: An absent node rejects the entire reorder.
        """
        ids = tuple(data.ordered_ids)
        current = await self.repo.lock_sort_positions(ids)
        if len(current) != len(ids):
            missing = next(id for id in ids if id not in current)
            self._check_for_id_existence(missing, None)
        requested = changed_positions(ids, current)
        if requested:
            await self.repo.set_sort_positions(requested)

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
        if "api_key" in changes:
            key = changes.pop("api_key")
            changes["api_key_ciphertext"] = await self._seal(key)
        node = await self._update(id, changes)
        return node

    async def _seal(self, key: SecretStr | None) -> str | None:
        ciphertext = None
        if key is not None:
            ciphertext = await self.credentials.seal(key)
            if ciphertext is None:
                raise ValidationException(
                    message="Node credential encryption is unavailable.",
                    message_code="node_credential_encryption_unavailable",
                    loc=["api_key"],
                )
        return ciphertext

    @handle_conflicts(entity="Node")
    @transactional
    async def _update(self, id: int, changes: dict) -> NodeModel:
        node = await self.repo.update_by_id(id, changes)
        return self._check_for_id_existence(id, node)

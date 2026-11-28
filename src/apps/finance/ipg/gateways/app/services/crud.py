"""Manage gateway accounts with their single-table repository."""

from papilio.infra.db.tools.conflicts import handle_conflicts
from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks
from papilio.types.constants import INT64_MAX

from ...domain.dtos.records import GatewayList, GatewayUpdate
from ...domain.enums.records import GatewayKind
from ...domain.models.records import GatewayModel
from ...infra.pg.repositories.crud import GatewayRepository


class GatewayService(IDChecks[GatewayModel]):
    entity = "IPGGateway"

    def __init__(self, repo: GatewayRepository) -> None:
        self.repo = repo

    @handle_conflicts(message="This gateway kind already exists.")
    @transactional
    async def create(self, data: GatewayModel) -> GatewayModel:
        """Store a gateway account with its prepared configuration.

        Args:
            data: Gateway metadata and encrypted provider credentials.

        Returns:
            The stored gateway account.
        """
        gateway = await self.repo.create(data)
        return gateway

    async def get_by_id(self, id: int) -> GatewayModel:
        """Read one account, including inactive accounts.

        Args:
            id: Gateway identity.

        Returns:
            The stored gateway account.

        Raises:
            NotFoundException: The gateway does not exist.
        """
        gateway = await self.find_by_id(id)
        return self._check_for_id_existence(id, gateway)

    async def find_by_id(self, id: int) -> GatewayModel | None:
        """Read an optional account for webhook authentication.

        Args:
            id: Gateway identity.

        Returns:
            The stored account or None when it is absent.
        """
        gateway = await self.repo.get_by_id(id)
        return gateway

    async def find_by_kind(self, kind: GatewayKind) -> GatewayModel | None:
        """Read the current account for the provider kind, if configured."""
        gateway = await self.repo.find_by_kind(kind)
        return gateway

    async def list(self, query: GatewayList) -> PagedType[GatewayModel]:
        """Read a filtered list for the panel.

        Args:
            query: Validated search, filters and page request.

        Returns:
            The matching page and unpaged count.
        """
        offset = min((query.page - 1) * query.per_page, INT64_MAX)
        page = await self.repo.list(query, offset=offset)
        return page

    @transactional
    async def update(self, id: int, data: GatewayUpdate) -> GatewayModel:
        """Apply an independent update to gateway metadata.

        Args:
            id: Gateway identity.
            data: Supplied metadata changes. Explicit null clears the icon.

        Returns:
            The updated gateway account.

        Raises:
            ValidationException: The patch contains no supported changes.
            NotFoundException: The gateway does not exist.
        """
        changes = self._check_not_empty_dict(data.to_row())
        gateway = await self.repo.update_by_id(id, changes)
        return self._check_for_id_existence(id, gateway)

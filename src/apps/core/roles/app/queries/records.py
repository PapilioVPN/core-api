"""Short role-permission reads through the owning native reader."""

from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks

from src.apps.core.roles.domain.dtos.records import (
    RoleBatchRead,
    RoleList,
)
from src.apps.core.roles.domain.results.details import (
    RoleAccess,
    RoleDetailsResult,
)
from src.apps.core.roles.infra.pg.repositories.reader import RoleReader


class RoleQuery(IDChecks[RoleDetailsResult]):
    entity = "Role"

    def __init__(self, reader: RoleReader) -> None:
        """Bind the request's reader without owning sessions or clients.

        Args:
            reader: Role-permission reader on the current native UoW.

        Returns:
            None.
        """
        self.reader = reader

    async def get_by_id(self, id: int) -> RoleDetailsResult:
        """Read a role and its scope permissions, requiring its existence.

        Args:
            id: Stored role identity.

        Returns:
            Materialized role details, including zero masks and inactive flags.

        Raises:
            NotFoundException: The role is absent.
        """
        role = await self.reader.get_by_id(id)
        role = self._check_for_id_existence(id, role)
        return role

    async def find_access(self, id: int) -> RoleAccess | None:
        """Read live authorization facts for a role.

        Args:
            id: Stored role identity.

        Returns:
            Role eligibility and active scope masks, or None when absent.
        """
        access = await self.reader.find_access(id)
        return access

    async def get_by_ids(self, data: RoleBatchRead) -> list[RoleDetailsResult]:
        """Read a bounded set of role details through the native batch path.

        Args:
            data: One to 100 validated IDs; repeated IDs are returned once.

        Returns:
            Materialized roles in ascending ID order; missing IDs are omitted.
        """
        roles = await self.reader.get_by_ids(data.ids)
        return roles

    async def list(self, query: RoleList) -> PagedType[RoleDetailsResult]:
        """List role details using application-owned pagination.

        Args:
            query: Native page/per_page with optional title and active flag.

        Returns:
            ID-ordered materialized roles with all stored scope assignments,
            and their matching role count before paging.
        """
        page = await self.reader.list(
            limit=query.per_page,
            offset=(query.page - 1) * query.per_page,
            title=query.title,
            is_active=query.is_active,
        )
        return page

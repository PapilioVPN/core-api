"""Role orchestration with native transactions and conflict handling."""

from collections.abc import Sequence

from papilio.infra.db.tools.conflicts import handle_conflicts
from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks

from src.apps.core.roles.domain.dtos.records import (
    RoleBatchRead,
    RoleCreate,
    RoleList,
    RoleUpdate,
)
from src.apps.core.roles.domain.models.records import RoleModel
from src.apps.core.roles.infra.pg.repositories.records import (
    RoleRepository,
)


class RoleService(IDChecks[RoleModel]):
    entity = "Role"

    def __init__(self, repo: RoleRepository) -> None:
        """Bind this request's role repository.

        Args:
            repo: Native PostgreSQL repository on the request's UoW.

        Returns:
            None.
        """
        self.repo = repo

    @handle_conflicts(entity="Role")
    @transactional
    async def create(self, data: RoleCreate) -> RoleModel:
        """Create a role with an exact user-defined key.

        Args:
            data: Validated role fields, including the initial active flag.

        Returns:
            The stored role with its database identity and timestamps.

        Raises:
            ConflictException: A role already has this exact key.
        """
        role = await self.repo.create(
            RoleModel(
                key=data.key,
                title=data.title,
                description=data.description,
                is_active=data.is_active,
            )
        )
        return role

    async def get_by_id(self, id: int) -> RoleModel:
        """Read a role that must exist.

        Args:
            id: Stored role identity.

        Returns:
            The role, including inactive records.

        Raises:
            NotFoundException: The identity is absent.
        """
        role = await self.repo.get_by_id(id)
        role = self._check_for_id_existence(id, role)
        return role

    async def find_by_id(self, id: int) -> RoleModel | None:
        """Look up a role without requiring its existence.

        Args:
            id: Stored role identity.

        Returns:
            The role, including inactive records; None when absent.
        """
        role = await self.repo.get_by_id(id)
        return role

    async def find_by_key(self, key: str) -> RoleModel | None:
        """Look up a role by its unchanged user-defined key.

        Args:
            key: Exact, case-sensitive role key.

        Returns:
            The role, including inactive records; None when absent.
        """
        role = await self.repo.find_by_key(key)
        return role

    async def get_by_ids(self, data: RoleBatchRead) -> Sequence[RoleModel]:
        """Read a bounded set of roles using one native set operation.

        Args:
            data: One to 100 validated IDs; repeated IDs produce one record.

        Returns:
            Stored roles, omitting missing IDs. Result order is unspecified.
        """
        roles = await self.repo.get_by_ids(data.ids)
        return roles

    async def list(self, query: RoleList) -> PagedType[RoleModel]:
        """List matching roles using application-owned pagination.

        Args:
            query: Native page/per_page and optional title/state filters.

        Returns:
            An ID-ordered page and its filtered total before pagination.
        """
        page = await self.repo.list(
            limit=query.per_page,
            offset=(query.page - 1) * query.per_page,
            title=query.title,
            is_active=query.is_active,
        )
        return page

    @transactional
    async def update(self, id: int, data: RoleUpdate) -> RoleModel:
        """Apply supplied changes while preserving the role key.

        Args:
            id: Stored role identity.
            data: Validated patch; description may be cleared.

        Returns:
            The updated role, preserving every omitted field.

        Raises:
            NotFoundException: The identity is absent.
            ValidationException: No update fields were supplied.
        """
        changes = self._check_not_empty_dict(data.to_row())
        role = await self.repo.update_by_id(id, changes)
        role = self._check_for_id_existence(id, role)
        return role

    @transactional
    async def remove(self, id: int) -> RoleModel:
        """Delete one role and cascade its scope assignments atomically.

        Args:
            id: Stored role identity.

        Returns:
            The role as it was before deletion; shared scopes remain intact.

        Raises:
            NotFoundException: The identity is absent.
        """
        role = await self.repo.remove_by_id(id)
        role = self._check_for_id_existence(id, role)
        return role

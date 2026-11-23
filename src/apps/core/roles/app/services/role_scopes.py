"""Assignment operations on one repository using native persistence."""

from collections.abc import Sequence

from papilio.infra.db.tools.conflicts import handle_conflicts
from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import Checks

from src.apps.core.roles.domain.dtos.role_scopes import (
    RoleScopeCreate,
    RoleScopeList,
    RoleScopeUpdate,
)
from src.apps.core.roles.domain.models.records import RoleScopeModel
from src.apps.core.roles.infra.pg.repositories.role_scopes import (
    RoleScopeRepository,
)


class RoleScopeService(Checks[RoleScopeModel]):
    entity = "RoleScope"

    def __init__(self, repo: RoleScopeRepository) -> None:
        """Bind the current request's assignment repository.

        Args:
            repo: Native repository on the owning request's UoW.

        Returns:
            None.
        """
        self.repo = repo

    @handle_conflicts(entity="RoleScope")
    @transactional
    async def create(
        self, role_id: int, data: RoleScopeCreate
    ) -> RoleScopeModel:
        """Create one scope assignment for the explicit parent role.

        Args:
            role_id: Parent role identity supplied separately from the body.
            data: Validated body containing scope_id and a mask in 0..15.

        Returns:
            The stored assignment, including a supplied zero mask.

        Raises:
            ConflictException: This role-scope pair already exists.
            IntegrityError: A referenced role or scope is absent.
        """
        assignment = await self.repo.create(
            RoleScopeModel(
                role_id=role_id,
                scope_id=data.scope_id,
                permissions=data.permissions,
            )
        )
        return assignment

    async def get(self, role_id: int, scope_id: int) -> RoleScopeModel:
        """Read one assignment that must belong to the parent role.

        Args:
            role_id: Parent role identity.
            scope_id: Scope identity within the parent role.

        Returns:
            The stored assignment without interpreting its mask.

        Raises:
            NotFoundException: No assignment matches both identities.
        """
        row = await self.repo.find_by_role_and_scope(role_id, scope_id)
        row = self._check_for_existence("scope_id", scope_id, row)
        return row

    async def find(self, role_id: int, scope_id: int) -> RoleScopeModel | None:
        """Look up an optional assignment matching parent and scope together.

        Args:
            role_id: Parent role identity.
            scope_id: Scope identity within the parent role.

        Returns:
            The stored assignment, or None when the pair is absent.
        """
        row = await self.repo.find_by_role_and_scope(role_id, scope_id)
        return row

    async def get_by_scope_ids(
        self, role_id: int, scope_ids: Sequence[int]
    ) -> Sequence[RoleScopeModel]:
        """Read a bounded set of assignments from one parent role.

        Args:
            role_id: Parent role identity, applied in the native query.
            scope_ids: Caller-bounded IDs; repeats produce one record.

        Returns:
            Matching assignments, omitting missing scopes; order unspecified.
        """
        rows = await self.repo.get_by_scope_ids(role_id, scope_ids)
        return rows

    async def list(
        self, role_id: int, query: RoleScopeList
    ) -> PagedType[RoleScopeModel]:
        """List one role's assignments with application-owned pagination.

        Args:
            role_id: Parent role identity supplied separately from the query.
            query: Native page/per_page and optional exact scope filter.

        Returns:
            ID-ordered assignments and their matching total before paging.
        """
        page = await self.repo.list(
            limit=query.per_page,
            offset=(query.page - 1) * query.per_page,
            role_id=role_id,
            scope_id=query.scope_id,
        )
        return page

    @transactional
    async def update(
        self, role_id: int, data: RoleScopeUpdate
    ) -> RoleScopeModel:
        """Replace one mask using the parent role and body scope identity.

        Args:
            role_id: Authoritative parent role identity from the path.
            data: Validated scope_id and required permissions, including zero.

        Returns:
            The updated assignment with both identities preserved.

        Raises:
            NotFoundException: No assignment matches both identities.
        """
        row = await self.repo.update_permissions(
            role_id, data.scope_id, data.permissions
        )
        row = self._check_for_existence("scope_id", data.scope_id, row)
        return row

    @transactional
    async def remove(self, role_id: int, scope_id: int) -> RoleScopeModel:
        """Delete one assignment within its authoritative parent role.

        Args:
            role_id: Parent role identity supplied by the path.
            scope_id: Scope identity supplied by the execution adapter.

        Returns:
            The removed assignment; its role and shared scope remain intact.

        Raises:
            NotFoundException: No assignment matches both identities.
        """
        row = await self.repo.remove_for_role(role_id, scope_id)
        row = self._check_for_existence("scope_id", scope_id, row)
        return row

    @handle_conflicts(entity="RoleScope")
    @transactional
    async def create_batch(
        self, role_id: int, items: Sequence[RoleScopeCreate]
    ) -> Sequence[RoleScopeModel]:
        """Persist accepted assignments with one native bulk insert.

        Args:
            role_id: Parent identity verified by the owning command.
            items: Bounded unique scope/mask pairs selected by the command.

        Returns:
            Actual inserted assignments; empty input produces no write.

        Raises:
            ConflictException: The pair already exists.
        """
        assignments = await self.repo.bulk_create(
            [
                RoleScopeModel(
                    role_id=role_id,
                    scope_id=item.scope_id,
                    permissions=item.permissions,
                )
                for item in items
            ]
        )
        return assignments

    @transactional
    async def update_batch(
        self, role_id: int, items: Sequence[RoleScopeUpdate]
    ) -> Sequence[RoleScopeModel]:
        """Replace accepted masks with one native composite-key bulk update.

        Args:
            role_id: Parent identity verified by the owning command.
            items: Bounded unique scope/mask pairs selected by the command.

        Returns:
            Actual updated assignments; unmatched pairs are omitted.
        """
        assignments = await self.repo.bulk_update_permissions(role_id, items)
        return assignments

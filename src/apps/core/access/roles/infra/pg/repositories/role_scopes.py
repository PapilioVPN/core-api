"""Native persistence for role-scope assignments."""

from collections.abc import Sequence

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.infra.db.tools.read import fetch_page
from papilio.schemas.results import PagedType
from sqlalchemy import and_, select
from sqlmodel import col

from src.apps.core.access.roles.domain.dtos.role_scopes import RoleScopeUpdate
from src.apps.core.access.roles.domain.models.records import RoleScopeModel
from src.apps.core.access.roles.infra.pg.tables import RoleScopeTable


class RoleScopeRepository(PGPersistenceRepository[RoleScopeModel]):
    table = RoleScopeTable

    async def find_by_role_and_scope(
        self, role_id: int, scope_id: int
    ) -> RoleScopeModel | None:
        """Read the assignment for an exact role-scope pair.

        Args:
            role_id: Stored role identity.
            scope_id: Stored scope identity.

        Returns:
            The assignment, including a zero mask; None when absent.
        """
        stmt = select(self.table).where(
            col(self.table.role_id) == role_id,
            col(self.table.scope_id) == scope_id,
        )
        result = await self.uow.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        limit: int,
        offset: int = 0,
        role_id: int | None = None,
        scope_id: int | None = None,
    ) -> PagedType[RoleScopeModel]:
        """Read an ID-ordered assignment page, filtered by either identity.

        Args:
            limit: Positive maximum number of assignments to retrieve.
            offset: Nonnegative number of matching assignments to skip.
            role_id: Optional exact role filter.
            scope_id: Optional exact scope filter, combined with role_id.

        Returns:
            Stored assignments and their matching total before pagination.

        Raises:
            ValueError: Limit is nonpositive or offset is negative.
        """
        stmt = select(self.table).order_by(col(self.table.id))
        if role_id is not None:
            stmt = stmt.where(col(self.table.role_id) == role_id)
        if scope_id is not None:
            stmt = stmt.where(col(self.table.scope_id) == scope_id)
        page = await fetch_page(self.uow, stmt, limit=limit, offset=offset)
        return page

    async def get_by_scope_ids(
        self, role_id: int, scope_ids: Sequence[int]
    ) -> Sequence[RoleScopeModel]:
        """Read a set of scopes belonging only to the given role.

        Args:
            role_id: Authoritative parent role identity.
            scope_ids: Bounded scope identities; duplicates are returned once.

        Returns:
            Stored assignments; missing scopes are omitted, order unspecified.
        """
        rows = await self.get_all(
            col(self.table.role_id) == role_id,
            col(self.table.scope_id).in_(scope_ids),
        )
        return rows

    async def update_permissions(
        self, role_id: int, scope_id: int, permissions: int
    ) -> RoleScopeModel | None:
        """Update one mask by its parent role and scope together.

        Args:
            role_id: Authoritative parent role identity.
            scope_id: Scope identity to match within the parent.
            permissions: Validated replacement mask, including zero.

        Returns:
            The updated assignment, or None when the pair is absent.
        """
        rows = await self.update(
            and_(
                col(self.table.role_id) == role_id,
                col(self.table.scope_id) == scope_id,
            ),
            {"permissions": permissions},
        )
        row = rows[0] if rows else None
        return row

    async def remove_for_role(
        self, role_id: int, scope_id: int
    ) -> RoleScopeModel | None:
        """Delete an assignment matching both parent and scope.

        Args:
            role_id: Authoritative parent role identity.
            scope_id: Scope identity to match within the parent.

        Returns:
            The deleted assignment, or None when the pair is absent.
        """
        rows = await self.remove(
            and_(
                col(self.table.role_id) == role_id,
                col(self.table.scope_id) == scope_id,
            )
        )
        row = rows[0] if rows else None
        return row

    async def bulk_update_permissions(
        self, role_id: int, data: Sequence[RoleScopeUpdate]
    ) -> Sequence[RoleScopeModel]:
        """Apply a bounded set of masks using native UPDATE FROM VALUES.

        Args:
            role_id: Parent role used in every composite match key.
            data: Validated scope/mask pairs with unique scope identities.

        Returns:
            Updated assignments only; unmatched pairs are omitted. The caller
            owns completeness policy and transaction commit or rollback.
        """
        columns = RoleScopeTable.__table__.c
        rows = [
            {
                "role_id": role_id,
                "scope_id": item.scope_id,
                "permissions": item.permissions,
            }
            for item in data
        ]
        assignments = await self.bulk_update(
            rows,
            key_columns=[columns.role_id, columns.scope_id],
            update_columns=[columns.permissions],
        )
        return assignments

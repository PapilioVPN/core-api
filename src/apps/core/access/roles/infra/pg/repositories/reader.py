"""Focused role reads with eagerly loaded scope permissions."""

from collections.abc import Sequence

from papilio.infra.db.repositories.backends.postgresql import PGReader
from papilio.infra.db.tools.read import fetch_page
from papilio.schemas.results import PagedType
from sqlmodel import col

from src.apps.core.access.roles.domain.results.details import (
    RoleAccess,
    RoleDetailsResult,
)
from src.apps.core.access.roles.infra.pg.mappers.details import RoleMapper
from src.apps.core.access.roles.infra.pg.sql.records import RoleReadSQL
from src.apps.core.access.roles.infra.pg.tables import RoleTable


class RoleReader(PGReader):
    async def find_access(self, id: int) -> RoleAccess | None:
        """Read only the fields used to evaluate the current role.

        Args:
            id: Stored role identity.

        Returns:
            Role eligibility and active scope masks, or None when missing.
            Roles without active grants retain an empty scope map.
        """
        stmt = RoleReadSQL.select_access(id)
        result = await self.uow.execute(stmt)
        rows = result.tuples().all()
        access = None
        if rows:
            access = RoleAccess(
                id=id,
                is_active=rows[0][0],
                scopes={
                    key: mask
                    for _, key, mask in rows
                    if key is not None and mask is not None
                },
            )
        return access

    async def get_by_id(self, id: int) -> RoleDetailsResult | None:
        """Read one role and all its stored scope assignments.

        Args:
            id: Stored role identity.

        Returns:
            A materialized result, including inactive and zero-mask records;
            None when the role is absent. No session is needed after return.
        """
        stmt = RoleReadSQL.select_roles().where(col(RoleTable.id) == id)
        result = await self.uow.execute(stmt)
        row = result.scalar_one_or_none()
        details = None if row is None else RoleMapper.to_result(row)
        return details

    async def get_by_ids(self, ids: Sequence[int]) -> list[RoleDetailsResult]:
        """Read a batch using a native IN selection and eager collection load.

        Args:
            ids: Bounded requested identities; duplicates are returned once.

        Returns:
            Materialized roles in ascending ID order; missing IDs are omitted.
            An empty input returns an empty list without executing SQL.
        """
        items: list[RoleDetailsResult] = []
        if ids:
            stmt = (
                RoleReadSQL.select_roles()
                .where(col(RoleTable.id).in_(ids))
                .order_by(col(RoleTable.id))
            )
            result = await self.uow.execute(stmt)
            items = [
                RoleMapper.to_result(row) for row in result.scalars().all()
            ]
        return items

    async def list(
        self,
        *,
        limit: int,
        offset: int = 0,
        title: str | None = None,
        is_active: bool | None = None,
    ) -> PagedType[RoleDetailsResult]:
        """Read a role page with its scope permissions and matching role count.

        Args:
            limit: Positive maximum number of roles, not assignments.
            offset: Nonnegative number of matching roles to skip.
            title: Literal case-insensitive role-title substring, or None.
            is_active: Optional stored role flag; scope flags are preserved.

        Returns:
            ID-ordered roles with assignments ordered by scope ID, and the
            matching role count before paging. No lazy values escape.

        Raises:
            ValueError: Limit is nonpositive or offset is negative.
        """
        stmt = RoleReadSQL.select_roles().order_by(col(RoleTable.id))
        if title is not None:
            stmt = stmt.where(
                col(RoleTable.title).icontains(title, autoescape=True)
            )
        if is_active is not None:
            stmt = stmt.where(col(RoleTable.is_active) == is_active)
        page = await fetch_page(self.uow, stmt, limit=limit, offset=offset)
        result = PagedType(
            items=[RoleMapper.to_result(row) for row in page.items],
            total_items=page.total_items,
        )
        return result

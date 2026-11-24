"""Native SQL construction for role and permission reads; no I/O."""

from typing import cast

from sqlalchemy import Select, and_, select
from sqlalchemy.orm import InstrumentedAttribute, selectinload
from sqlmodel import col

from src.apps.core.access.roles.infra.pg.tables import (
    RoleScopeTable,
    RoleTable,
)
from src.apps.core.access.scopes.infra.pg.tables import ScopeTable


class RoleReadSQL:
    @staticmethod
    def select_access(id: int) -> Select[tuple[bool, str | None, int | None]]:
        """Select role eligibility and current scopes in one statement.

        Args:
            id: Stored role identity.

        Returns:
            A selection retaining roles with no active scopes.
        """
        stmt = (
            select(
                col(RoleTable.is_active),
                col(ScopeTable.key),
                col(RoleScopeTable.permissions),
            )
            .select_from(RoleTable)
            .outerjoin(
                RoleScopeTable,
                col(RoleScopeTable.role_id) == col(RoleTable.id),
            )
            .outerjoin(
                ScopeTable,
                and_(
                    col(ScopeTable.id) == col(RoleScopeTable.scope_id),
                    col(ScopeTable.is_active).is_(True),
                ),
            )
            .where(col(RoleTable.id) == id)
        )
        return cast(Select[tuple[bool, str | None, int | None]], stmt)

    @staticmethod
    def select_roles() -> Select[tuple[RoleTable]]:
        """Build the common role selection with explicit eager projections.

        Args:
            None.

        Returns:
            An unexecuted selection with collection and scope eager loading.
        """
        stmt = (
            select(RoleTable)
            .options(
                selectinload(
                    cast(
                        InstrumentedAttribute[list[RoleScopeTable]],
                        RoleTable.scope_assignments,
                    )
                )
                .load_only(
                    cast(InstrumentedAttribute[int], RoleScopeTable.scope_id),
                    cast(
                        InstrumentedAttribute[int], RoleScopeTable.permissions
                    ),
                )
                .joinedload(
                    cast(
                        InstrumentedAttribute[ScopeTable], RoleScopeTable.scope
                    )
                )
                .load_only(
                    cast(InstrumentedAttribute[int], ScopeTable.id),
                    cast(InstrumentedAttribute[str], ScopeTable.key),
                    cast(InstrumentedAttribute[str], ScopeTable.title),
                    cast(InstrumentedAttribute[bool], ScopeTable.is_active),
                )
            )
            .execution_options(populate_existing=True)
        )
        return stmt

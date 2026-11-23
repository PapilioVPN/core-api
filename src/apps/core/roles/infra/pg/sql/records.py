"""Native SQL construction for role and permission reads; no I/O."""

from typing import cast

from sqlalchemy import Select, select
from sqlalchemy.orm import InstrumentedAttribute, selectinload

from src.apps.core.roles.infra.pg.tables import (
    RoleScopeTable,
    RoleTable,
)
from src.apps.core.scopes.infra.pg.tables import ScopeTable


class RoleReadSQL:
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

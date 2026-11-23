"""Explicit adaptation of loaded role rows into materialized domain results."""

from src.apps.core.roles.domain.results.details import (
    RoleDetailsResult,
    ScopePermissionResult,
)
from src.apps.core.roles.infra.pg.tables import RoleTable


class RoleMapper:
    @staticmethod
    def to_result(row: RoleTable) -> RoleDetailsResult:
        """Materialize the explicitly loaded role and scope fields.

        Args:
            row: Role whose scope assignments and scope summaries are loaded.

        Returns:
            Typed stored facts with no ORM or session-dependent values.
        """
        result = RoleDetailsResult(
            id=row.id,
            key=row.key,
            title=row.title,
            description=row.description,
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
            scopes=[
                ScopePermissionResult(
                    scope_id=assignment.scope_id,
                    key=assignment.scope.key,
                    title=assignment.scope.title,
                    is_active=assignment.scope.is_active,
                    permissions=assignment.permissions,
                )
                for assignment in row.scope_assignments
            ],
        )
        return result

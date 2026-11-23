"""Administrator-owned access claims from checked account and role facts."""

from uuid import UUID

from pydantic import JsonValue

from src.apps.core.roles.domain.results.records import RoleDetailsResult
from src.apps.core.tokens.domain.models.tokens import TokenIdentity


def active_scopes(role: RoleDetailsResult) -> dict[str, int]:
    """Read permission masks for the role's currently active scopes."""
    return {
        scope.key: scope.permissions
        for scope in role.scopes
        if scope.is_active
    }


def admin_token_identity(
    user_id: int, role: RoleDetailsResult, session_id: UUID
) -> TokenIdentity:
    """Build claims using active scopes without interpreting their bitmask.

    Args:
        user_id: Authoritative active account ID.
        role: Materialized active current role, including scope activity.
        session_id: Stable identity of this login across refreshes.

    Returns:
        Admin token identity preserving empty scope maps and zero masks.
    """
    scopes: dict[str, JsonValue] = dict(active_scopes(role))
    result = TokenIdentity(
        subject=str(user_id),
        audience="admin",
        claims={
            "role_id": role.id,
            "scopes": scopes,
        },
        session_id=session_id,
    )
    return result

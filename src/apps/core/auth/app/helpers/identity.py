"""Administrator-owned access claims from checked account and role facts."""

from uuid import UUID

from pydantic import JsonValue

from src.apps.core.roles.domain.results.records import RoleAccess
from src.apps.core.tokens.domain.models.tokens import TokenIdentity


def admin_token_identity(
    user_id: int, role: RoleAccess, session_id: UUID
) -> TokenIdentity:
    """Build claims using active scopes without interpreting their bitmask.

    Args:
        user_id: Authoritative active account ID.
        role: Current role including its active scope masks.
        session_id: Stable identity of this login across refreshes.

    Returns:
        Admin token identity preserving empty scope maps and zero masks.
    """
    scopes: dict[str, JsonValue] = dict(role.scopes)
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

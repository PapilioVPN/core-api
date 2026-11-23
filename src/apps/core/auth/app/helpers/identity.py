"""Administrator-owned access claims from checked account and role facts."""

from src.apps.core.roles.domain.results.records import RoleDetailsResult
from src.apps.core.tokens.domain.models.tokens import TokenIdentity


def admin_token_identity(
    user_id: int, role: RoleDetailsResult
) -> TokenIdentity:
    """Build claims using active scopes without interpreting their bitmask.

    Args:
        user_id: Authoritative active account ID.
        role: Materialized active current role, including scope activity.

    Returns:
        Admin token identity preserving empty scope maps and zero masks.
    """
    result = TokenIdentity(
        subject=str(user_id),
        audience="admin",
        claims={
            "role_id": role.id,
            "scopes": {
                scope.key: scope.permissions
                for scope in role.scopes
                if scope.is_active
            },
        },
    )
    return result

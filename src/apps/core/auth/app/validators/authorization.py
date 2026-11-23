"""Pure administrator permission checks."""

from papilio.errors.exceptions import ForbiddenException

from src.apps.core.auth.domain.enums.permissions import AdminPermission
from src.apps.core.auth.domain.results.identity import AdminIdentity


def validate_admin_permission(
    identity: AdminIdentity, scope: str, permission: AdminPermission
) -> None:
    """Require every requested bit in the exact access-token scope.

    Args:
        identity: Verified administrator permission snapshot.
        scope: Exact group key; another scope grants nothing here.
        permission: Required operation bits; zero never grants access.

    Returns:
        None when permitted, otherwise a native forbidden error.
    """
    mask = identity.scopes.get(scope, 0)
    if not permission or mask & permission != permission:
        raise ForbiddenException(
            message="Insufficient administrator permissions",
            message_code="admin_permission_required",
        )

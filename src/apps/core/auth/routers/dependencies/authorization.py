"""Native HTTP permissions for administrator operations."""

from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import Depends, Request

from src.apps.core.auth.app.validators.authorization import (
    validate_admin_permission,
)
from src.apps.core.auth.domain.enums.permissions import AdminPermission
from src.apps.core.auth.domain.results.identity import AdminIdentity
from src.apps.core.auth.routers.dependencies.identity import (
    current_admin,
)


def require_admin(
    scope: str,
) -> Callable[..., Coroutine[Any, Any, AdminIdentity]]:
    """Bind the owning group while HTTP methods specify the operation.

    Args:
        scope: Explicit capability group, independent of URL spelling.

    Returns:
        Native injectable dependency; unknown methods require no valid grant.
    """

    async def authorize(
        request: Request,
        identity: Annotated[AdminIdentity, Depends(current_admin)],
    ) -> AdminIdentity:
        """Verify current eligibility and the method's operation mask.

        Args:
            request: Native HTTP request; client body cannot choose scope/bits.
            identity: Verified session and current permissions.

        Returns:
            Authorized administrator identity and current scopes.
        """
        permission = {
            "GET": AdminPermission.READ,
            "HEAD": AdminPermission.READ,
            "POST": AdminPermission.CREATE,
            "PUT": AdminPermission.UPDATE,
            "PATCH": AdminPermission.UPDATE,
            "DELETE": AdminPermission.DELETE,
        }.get(request.method, AdminPermission(0))
        validate_admin_permission(identity, scope, permission)
        return identity

    return authorize

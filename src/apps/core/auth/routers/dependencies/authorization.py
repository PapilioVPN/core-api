"""Group-owned native HTTP dependencies for administrator operations."""

from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import Depends, Request

from src.apps.core.auth.app.interfaces.authorization import (
    IAdminAuthorizationService,
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

    @inject
    async def authorize(
        request: Request,
        identity: Annotated[AdminIdentity, Depends(current_admin)],
        service: FromDishka[IAdminAuthorizationService],
    ) -> AdminIdentity:
        """Verify current eligibility and the method's operation mask.

        Args:
            request: Native HTTP request; client body cannot choose scope/bits.
            identity: Verified access credential and permission snapshot.
            service: Request-scoped authorization owner.

        Returns:
            Authorized administrator identity, preserving its token scopes.
        """
        permission = {
            "GET": AdminPermission.READ,
            "HEAD": AdminPermission.READ,
            "POST": AdminPermission.CREATE,
            "PUT": AdminPermission.UPDATE,
            "PATCH": AdminPermission.UPDATE,
            "DELETE": AdminPermission.DELETE,
        }.get(request.method, AdminPermission(0))
        result = await service.check(identity, scope, permission)
        return result

    return authorize

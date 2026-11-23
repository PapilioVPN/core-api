"""HTTP bearer extraction and native request-scoped identity injection."""

from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from papilio.core import resources
from papilio.errors.exceptions import UnAuthorizedException

from src.apps.core.auth.app.interfaces.services import (
    IAdminIdentityService,
)
from src.apps.core.auth.domain.results.identity import AdminIdentity


@inject
async def current_admin(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(HTTPBearer(auto_error=False)),
    ],
    service: FromDishka[IAdminIdentityService],
) -> AdminIdentity:
    """Resolve the bearer credential using the request's identity service.

    Args:
        credentials: Native bearer extraction, or None when absent/invalid.
        service: Injected administrator access-token verification contract.

    Returns:
        Verified account identity with active session and current grants.

    Raises:
        UnAuthorizedException: Bearer credentials are missing or invalid.
    """
    if credentials is None:
        raise UnAuthorizedException(
            message="missing authentication token",
            message_code=resources.MISSING_TOKEN,
        )
    identity = await service.resolve(credentials.credentials)
    return identity

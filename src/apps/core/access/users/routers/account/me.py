"""Self-account resources through the existing profile app contracts."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from papilio.api.responses.envelope import APIResponse

from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.auth.routers.dependencies.identity import (
    current_admin,
)
from src.apps.core.access.users.app.interfaces.commands import (
    IUserProfileCommand,
)
from src.apps.core.access.users.app.interfaces.services import (
    IUserProfileService,
)
from src.apps.core.access.users.domain.dtos.profile import UserProfileUpdate
from src.apps.core.access.users.routers.schemas.profile import (
    UserProfileOutput,
)

router = APIRouter(
    prefix="/admin/account/me",
    route_class=DishkaRoute,
)


@router.get("", response_model=APIResponse[UserProfileOutput, None])
async def get_me(
    identity: Annotated[AdminIdentity, Depends(current_admin)],
    service: FromDishka[IUserProfileService],
) -> APIResponse[UserProfileOutput, None]:
    """Read the authenticated account with its current permissions.

    Args:
        identity: Verified bearer identity supplied by authentication.
        service: Request-scoped current-profile reader.

    Returns:
        Profile output without credentials, preserving payload scope masks.

    Raises:
        UnAuthorizedException: Authentication or account/role checks fail.
    """
    profile = await service.get_me(identity)
    output = UserProfileOutput.from_obj(profile)
    return APIResponse[UserProfileOutput, None].from_data(output)


@router.patch("", response_model=APIResponse[UserProfileOutput, None])
async def patch_me(
    data: UserProfileUpdate,
    identity: Annotated[AdminIdentity, Depends(current_admin)],
    command: FromDishka[IUserProfileCommand],
) -> APIResponse[UserProfileOutput, None]:
    """Update the authenticated account's supplied name fields.

    Args:
        data: Restricted name patch; omitted fields stay unchanged.
        identity: Verified bearer identity, not a caller-selected account ID.
        command: Request-scoped transactional self-profile command.

    Returns:
        Updated profile output with the current role and scopes.

    Raises:
        UnAuthorizedException: Authentication or account/role checks fail.
        ValidationException: No recognized profile fields were supplied.
    """
    profile = await command.update(identity, data)
    output = UserProfileOutput.from_obj(profile)
    return APIResponse[UserProfileOutput, None].from_data(output)

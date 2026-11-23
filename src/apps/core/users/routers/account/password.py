"""Verify the current password before changing the signed-in account."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from papilio.api.responses.envelope import APIResponse

from src.apps.core.auth.domain.results.identity import AdminIdentity
from src.apps.core.auth.routers.dependencies.identity import current_admin
from src.apps.core.users.app.interfaces.commands import (
    IUserPasswordCommand,
)
from src.apps.core.users.domain.dtos.records import UserPasswordUpdate
from src.apps.core.users.routers.schemas.records import UserOutput

router = APIRouter(
    prefix="/admin/account/me/password",
    route_class=DishkaRoute,
)


@router.patch("", response_model=APIResponse[UserOutput, None])
async def patch_password(
    data: UserPasswordUpdate,
    identity: Annotated[AdminIdentity, Depends(current_admin)],
    command: FromDishka[IUserPasswordCommand],
) -> APIResponse[UserOutput, None]:
    """Change the authenticated user's password through the existing owner.

    Args:
        data: Raw password validated by native PasswordType.
        identity: Verified access identity for the current account.
        command: Current-account eligibility, hashing and persistence owner.

    Returns:
        Updated account output without raw passwords or stored hashes.

    Raises:
        UnAuthorizedException: Access, password or account eligibility fails.
    """
    user = await command.update_me(identity, data)
    output = UserOutput.from_obj(user)
    return APIResponse[UserOutput, None].from_data(output)

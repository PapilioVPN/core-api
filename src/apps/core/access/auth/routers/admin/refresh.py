"""Refresh credentials authorize rotation independently of expired access."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter
from papilio.api.responses.envelope import APIResponse

from src.apps.core.access.auth.app.interfaces.commands import (
    ITokenLogoutCommand,
    ITokenRefreshCommand,
)
from src.apps.core.access.auth.domain.dtos.refresh import TokenRefresh
from src.apps.core.access.auth.routers.schemas.tokens import TokenPairOutput

router = APIRouter(
    prefix="/admin/auth/refresh-tokens",
    route_class=DishkaRoute,
)


@router.post("", response_model=APIResponse[TokenPairOutput, None])
async def post_refresh_tokens(
    data: TokenRefresh, command: FromDishka[ITokenRefreshCommand]
) -> APIResponse[TokenPairOutput, None]:
    """Exchange one refresh for a new pair after current account checks.

    Args:
        data: Required refresh credential; access/sudo headers are not needed.
        command: Injected rotation owner using the request's native SQL UoW.

    Returns:
        Access/refresh pair only after the owning transaction commits.

    Raises:
        UnAuthorizedException: Credential was rejected or already consumed.
        Exception: Policy/SQL/signing errors propagate; no pair is returned.
    """
    pair = await command.refresh(data)
    return APIResponse[TokenPairOutput, None].from_data(
        TokenPairOutput.from_obj(pair)
    )


@router.delete("", response_model=APIResponse[None, None])
async def delete_refresh_tokens(
    data: TokenRefresh, command: FromDishka[ITokenLogoutCommand]
) -> APIResponse[None, None]:
    """Close the session of the supplied unused refresh credential.

    Args:
        data: Required refresh credential; no Bearer/sudo header is needed.
        command: Request-local revocation owner using the native SQL UoW.

    Returns:
        Success after commit, including repeated revocation. Root null fields
        are omitted by the native response envelope.

    Raises:
        UnAuthorizedException: The refresh credential fails verification.
        Exception: Persistence/commit failures propagate without success.
    """
    await command.logout(data)
    return APIResponse[None, None](success=True)

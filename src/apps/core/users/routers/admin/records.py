"""User resources with password-verified self-account password changes."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType

from src.apps.core.auth.domain.results.identity import AdminIdentity
from src.apps.core.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.core.users.app.interfaces.commands import (
    IUserCreateCommand,
    IUserPasswordCommand,
    IUserRoleCommand,
)
from src.apps.core.users.app.interfaces.services import IUserService
from src.apps.core.users.domain.dtos.password import UserPasswordUpdate
from src.apps.core.users.domain.dtos.records import (
    UserCreate,
    UserList,
    UserRoleUpdate,
    UserUpdate,
)
from src.apps.core.users.routers.dependencies.account import (
    current_account,
    user_profile_patch,
)
from src.apps.core.users.routers.schemas.records import UserOutput

router = APIRouter(
    prefix="/admin/users",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("access"))],
)


@router.post("", response_model=APIResponse[UserOutput, None], status_code=201)
async def post_user(
    data: UserCreate,
    command: FromDishka[IUserCreateCommand],
) -> APIResponse[UserOutput, None]:
    """Create an account through command-owned role checks and hashing.

    Args:
        data: Native validated account input with an optional raw password.
        command: Request-scoped user creation contract.

    Returns:
        The created account HTTP output without raw or hashed credentials.

    Raises:
        NotFoundException: The referenced role does not exist.
        ConflictException: The mobile already belongs to an account.
    """
    user = await command.create(data)
    output = UserOutput.from_obj(user)
    return APIResponse[UserOutput, None].from_data(output)


@router.patch("/{id}", response_model=APIResponse[UserOutput, None])
async def patch_user(
    id: IdType,
    data: Annotated[UserUpdate, Depends(user_profile_patch)],
    service: FromDishka[IUserService],
) -> APIResponse[UserOutput, None]:
    """Update supplied profile fields through the owning service.

    Args:
        id: Internal user identity validated from the public path by Papilio.
        data: Profile patch; contact fields are temporarily rejected.
        service: Request-scoped user service contract.

    Returns:
        The updated account HTTP output without credentials.

    Raises:
        ValidationException: The recognized profile patch is empty.
        NotFoundException: The user does not exist.
        ConflictException: Another user has the supplied mobile.
    """
    user = await service.update(id, data)
    output = UserOutput.from_obj(user)
    return APIResponse[UserOutput, None].from_data(output)


@router.get("", response_model=APIResponse[UserOutput, PagerMeta])
async def get_users(
    query: Annotated[UserList, Query()],
    service: FromDishka[IUserService],
) -> APIResponse[UserOutput, PagerMeta]:
    """Read a filtered page of accounts without credentials.

    Args:
        query: Native page/per_page and search, role and active filters.
        service: Request-scoped user service contract.

    Returns:
        User HTTP outputs and native paging metadata, including empty pages.
    """
    page = await service.list(query)
    output = UserOutput.from_objs(page.items)
    return APIResponse[UserOutput, PagerMeta](
        success=True,
        data=output,
        meta=PagerMeta.from_total(
            query.page, query.per_page, page.total_items
        ),
    )


@router.get("/{id}", response_model=APIResponse[UserOutput, None])
async def get_user(
    id: IdType,
    service: FromDishka[IUserService],
) -> APIResponse[UserOutput, None]:
    """Read one account without exposing its stored password hash.

    Args:
        id: Internal user identity validated from the public path by Papilio.
        service: Request-scoped user service contract.

    Returns:
        The account HTTP output, preserving nullable email and inactive state.

    Raises:
        NotFoundException: The user does not exist.
    """
    user = await service.get_by_id(id)
    output = UserOutput.from_obj(user)
    return APIResponse[UserOutput, None].from_data(output)


@router.delete("/{id}", response_model=APIResponse[UserOutput, None])
async def delete_user(
    id: IdType,
    service: FromDishka[IUserService],
) -> APIResponse[UserOutput, None]:
    """Delete one account through its owning service.

    Args:
        id: Internal user identity validated from the public path by Papilio.
        service: Request-scoped user service contract.

    Returns:
        The previous account HTTP output without credentials.

    Raises:
        NotFoundException: The user does not exist.
    """
    user = await service.remove(id)
    output = UserOutput.from_obj(user)
    return APIResponse[UserOutput, None].from_data(output)


@router.patch("/{id}/role", response_model=APIResponse[UserOutput, None])
async def patch_user_role(
    id: IdType,
    data: UserRoleUpdate,
    command: FromDishka[IUserRoleCommand],
) -> APIResponse[UserOutput, None]:
    """Replace an account's role through the dedicated role command.

    Args:
        id: Internal user identity validated from the public path by Papilio.
        data: Required target role identity from the request body.
        command: Request-scoped role command checking role existence.

    Returns:
        The updated account HTTP output without credentials.

    Raises:
        NotFoundException: The user or referenced role does not exist.
    """
    user = await command.update(id, data)
    output = UserOutput.from_obj(user)
    return APIResponse[UserOutput, None].from_data(output)


@router.patch("/{id}/password", response_model=APIResponse[UserOutput, None])
async def patch_user_password(
    data: UserPasswordUpdate,
    identity: Annotated[AdminIdentity, Depends(current_account)],
    command: FromDishka[IUserPasswordCommand],
) -> APIResponse[UserOutput, None]:
    """Change the current account password after current-password verification.

    Args:
        identity: Matching path and signed-in account identity.
        data: Required raw password validated by Papilio's PasswordType.
        command: Request-scoped password command owning native hashing.

    Returns:
        The updated account HTTP output without raw or hashed credentials.

    Raises:
        UnAuthorizedException: Account or role is unavailable.
        ForbiddenException: Sudo is missing or the target is another account.
    """
    user = await command.update_me(identity, data)
    output = UserOutput.from_obj(user)
    return APIResponse[UserOutput, None].from_data(output)

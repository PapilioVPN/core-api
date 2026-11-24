"""Role resources; access dependencies are deferred by agreement."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.core.access.roles.app.interfaces.commands import (
    IRoleRemoveCommand,
)
from src.apps.core.access.roles.app.interfaces.queries import IRoleQuery
from src.apps.core.access.roles.app.interfaces.services import IRoleService
from src.apps.core.access.roles.domain.dtos.records import (
    RoleCreate,
    RoleList,
    RoleUpdate,
)
from src.apps.core.access.roles.routers.schemas.records import (
    RoleDetailsOutput,
    RoleOutput,
)

router = APIRouter(
    prefix="/admin/roles",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("access"))],
)


@router.post("", response_model=APIResponse[RoleOutput, None], status_code=201)
async def post_role(
    data: RoleCreate,
    service: FromDishka[IRoleService],
) -> APIResponse[RoleOutput, None]:
    """Register one user-defined access role.

    Args:
        data: Native validated role fields.
        service: Request-scoped role service contract.

    Returns:
        Native envelope containing the created role's HTTP output.
    """
    role = await service.create(data)
    output = RoleOutput.from_obj(role)
    return APIResponse[RoleOutput, None].from_data(output)


@router.get("", response_model=APIResponse[RoleDetailsOutput, PagerMeta])
async def get_roles(
    query: Annotated[RoleList, Query()],
    service: FromDishka[IRoleQuery],
) -> APIResponse[RoleDetailsOutput, PagerMeta]:
    """Read a page of roles with optional title and active-state filters.

    Args:
        query: Native page/per_page and search DTO, forwarded unchanged.
        service: Request-scoped role details query contract.

    Returns:
        Role HTTP outputs and native pagination metadata.
    """
    page = await service.list(query)
    output = RoleDetailsOutput.from_objs(page.items)
    return APIResponse[RoleDetailsOutput, PagerMeta](
        success=True,
        data=output,
        meta=PagerMeta.from_total(
            query.page, query.per_page, page.total_items
        ),
    )


@router.get("/{id}", response_model=APIResponse[RoleDetailsOutput, None])
async def get_role(
    id: IdType,
    service: FromDishka[IRoleQuery],
) -> APIResponse[RoleDetailsOutput, None]:
    """Read one role by its native positive database identity.

    Args:
        id: Native validated role identity.
        service: Request-scoped role details query contract.

    Returns:
        The role HTTP output in the native response envelope.
    """
    role = await service.get_by_id(id)
    output = RoleDetailsOutput.from_obj(role)
    return APIResponse[RoleDetailsOutput, None].from_data(output)


@router.patch("/{id}", response_model=APIResponse[RoleOutput, None])
async def patch_role(
    id: IdType,
    data: RoleUpdate,
    service: FromDishka[IRoleService],
) -> APIResponse[RoleOutput, None]:
    """Update supplied role fields while preserving its key.

    Args:
        id: Native validated role identity.
        data: Validated patch; omission and explicit null remain distinct.
        service: Request-scoped role service contract.

    Returns:
        The updated role HTTP output in the native response envelope.
    """
    role = await service.update(id, data)
    output = RoleOutput.from_obj(role)
    return APIResponse[RoleOutput, None].from_data(output)


@router.delete("/{id}", response_model=APIResponse[RoleOutput, None])
async def delete_role(
    id: IdType,
    command: FromDishka[IRoleRemoveCommand],
) -> APIResponse[RoleOutput, None]:
    """Delete an unreferenced role and return its previous state.

    Args:
        id: Native validated role identity.
        command: Request-scoped removal contract checking user references.

    Returns:
        The removed role HTTP output in the native response envelope.

    Raises:
        ValidationException: Any account still references the role.
        NotFoundException: The role is absent.
    """
    role = await command.remove(id)
    output = RoleOutput.from_obj(role)
    return APIResponse[RoleOutput, None].from_data(output)

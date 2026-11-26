"""Role-scope resources with explicit parent paths and body identities."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Body, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType

from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.core.access.auth.routers.dependencies.identity import (
    current_admin,
)
from src.apps.core.access.roles.app.interfaces.commands import (
    IRoleScopeBatchCreateCommand,
    IRoleScopeBatchUpdateCommand,
    IRoleScopeCreateCommand,
    IRoleScopeRemoveCommand,
    IRoleScopeUpdateCommand,
)
from src.apps.core.access.roles.app.interfaces.services import (
    IRoleScopeService,
)
from src.apps.core.access.roles.domain.dtos.role_scopes import (
    RoleScopeBatchCreate,
    RoleScopeBatchUpdate,
    RoleScopeCreate,
    RoleScopeList,
    RoleScopeUpdate,
)
from src.apps.core.access.roles.routers.schemas.role_scopes import (
    RoleScopeOutput,
)

router = APIRouter(
    prefix="/admin/roles/{role_id}/scopes",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("access"))],
)

Actor = Annotated[AdminIdentity, Depends(current_admin)]


@router.post(
    "", response_model=APIResponse[RoleScopeOutput, None], status_code=201
)
async def post_role_scope(
    role_id: IdType,
    data: RoleScopeCreate,
    actor: Actor,
    command: FromDishka[IRoleScopeCreateCommand],
) -> APIResponse[RoleScopeOutput, None]:
    """Assign one scope to an existing role.

    Args:
        role_id: Native validated parent identity from the path.
        data: Scope identity and permissions from the body.
        actor: The authenticated operator making the assignment.
        command: Request-scoped owner of checks and assignment writes.

    Returns:
        The created assignment in Papilio's native envelope.
    """
    row = await command.create(role_id, data, actor_id=actor.user_id)
    output = RoleScopeOutput.from_obj(row)
    return APIResponse[RoleScopeOutput, None].from_data(output)


@router.get("", response_model=APIResponse[RoleScopeOutput, PagerMeta])
async def get_role_scopes(
    role_id: IdType,
    query: Annotated[RoleScopeList, Query()],
    service: FromDishka[IRoleScopeService],
) -> APIResponse[RoleScopeOutput, PagerMeta]:
    """Read a page of assignments restricted to the parent role.

    Args:
        role_id: Native validated parent role identity.
        query: Native page/per_page and optional exact scope filter.
        service: Request-scoped assignment read contract.

    Returns:
        Assignment outputs and native pagination metadata; no matches is empty.
    """
    page = await service.list(role_id, query)
    output = RoleScopeOutput.from_objs(page.items)
    return APIResponse[RoleScopeOutput, PagerMeta](
        success=True,
        data=output,
        meta=PagerMeta.from_total(
            query.page, query.per_page, page.total_items
        ),
    )


@router.patch("", response_model=APIResponse[RoleScopeOutput, None])
async def patch_role_scope(
    role_id: IdType,
    data: RoleScopeUpdate,
    actor: Actor,
    command: FromDishka[IRoleScopeUpdateCommand],
) -> APIResponse[RoleScopeOutput, None]:
    """Replace an assigned scope's mask within one role.

    Args:
        role_id: Authoritative parent identity from the path.
        data: Body scope_id and replacement mask, including zero.
        actor: The authenticated operator changing the mask.
        command: Request-scoped owner of checks and assignment writes.

    Returns:
        The updated assignment in the native envelope.
    """
    row = await command.update(role_id, data, actor_id=actor.user_id)
    output = RoleScopeOutput.from_obj(row)
    return APIResponse[RoleScopeOutput, None].from_data(output)


@router.delete("", response_model=APIResponse[RoleScopeOutput, None])
async def delete_role_scope(
    role_id: IdType,
    scope_id: Annotated[IdType, Body(embed=True)],
    actor: Actor,
    command: FromDishka[IRoleScopeRemoveCommand],
) -> APIResponse[RoleScopeOutput, None]:
    """Remove an assignment identified by its parent path and body scope.

    Args:
        role_id: Native validated parent identity from the path.
        scope_id: Native validated body field; the body is {"scope_id": id}.
        actor: The authenticated operator removing the assignment.
        command: Request-scoped owner of checks and assignment writes.

    Returns:
        The removed assignment; its parent and shared scope remain intact.
    """
    row = await command.remove(role_id, scope_id, actor_id=actor.user_id)
    output = RoleScopeOutput.from_obj(row)
    return APIResponse[RoleScopeOutput, None].from_data(output)


@router.post("/batch", response_model=APIResponse[RoleScopeOutput, None])
async def post_role_scopes_batch(
    role_id: IdType,
    data: RoleScopeBatchCreate,
    actor: Actor,
    command: FromDishka[IRoleScopeBatchCreateCommand],
) -> APIResponse[RoleScopeOutput, None]:
    """Assign valid scopes in bulk and report rejected input items.

    Args:
        role_id: Parent role checked by the command before any mutation.
        data: One to 100 validated scope/mask inputs in body order.
        actor: The authenticated operator making the assignments.
        command: Request-scoped owner of pre-reads and native bulk writes.

    Returns:
        Created assignment outputs in data and indexed native root errors.
        All-rejected input retains data=[] and its per-item errors.
    """
    batch = await command.create_batch(role_id, data, actor_id=actor.user_id)
    output = RoleScopeOutput.from_objs(batch.items)
    return APIResponse[RoleScopeOutput, None].from_data(
        output, errors=batch.errors
    )


@router.patch("/batch", response_model=APIResponse[RoleScopeOutput, None])
async def patch_role_scopes_batch(
    role_id: IdType,
    data: RoleScopeBatchUpdate,
    actor: Actor,
    command: FromDishka[IRoleScopeBatchUpdateCommand],
) -> APIResponse[RoleScopeOutput, None]:
    """Replace valid assigned masks in bulk and report rejected items.

    Args:
        role_id: Parent role checked by the command before any mutation.
        data: One to 100 validated body scope/mask replacements.
        actor: The authenticated operator changing the masks.
        command: Request-scoped owner of pre-reads and native bulk writes.

    Returns:
        Updated assignment outputs in data and indexed native root errors.
        Valid zero masks and empty success collections are preserved.
    """
    batch = await command.update_batch(role_id, data, actor_id=actor.user_id)
    output = RoleScopeOutput.from_objs(batch.items)
    return APIResponse[RoleScopeOutput, None].from_data(
        output, errors=batch.errors
    )

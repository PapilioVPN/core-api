"""Scope resources; access dependencies are deferred by agreement."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.core.access.scopes.app.interfaces.services import IScopeService
from src.apps.core.access.scopes.domain.dtos.records import (
    ScopeCreate,
    ScopeList,
    ScopeUpdate,
)
from src.apps.core.access.scopes.routers.schemas.records import ScopeOutput

router = APIRouter(
    prefix="/admin/scopes",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("access"))],
)


@router.post(
    "", response_model=APIResponse[ScopeOutput, None], status_code=201
)
async def post_scope(
    data: ScopeCreate,
    service: FromDishka[IScopeService],
) -> APIResponse[ScopeOutput, None]:
    """Register one user-defined access scope.

    Args:
        data: Native validated scope fields.
        service: Request-scoped scope service contract.

    Returns:
        Native envelope containing the created scope's HTTP output.
    """
    scope = await service.create(data)
    output = ScopeOutput.from_obj(scope)
    return APIResponse[ScopeOutput, None].from_data(output)


@router.get("", response_model=APIResponse[ScopeOutput, PagerMeta])
async def get_scopes(
    query: Annotated[ScopeList, Query()],
    service: FromDishka[IScopeService],
) -> APIResponse[ScopeOutput, PagerMeta]:
    """Read a page of scopes with optional title and active-state filters.

    Args:
        query: Native page/per_page and search DTO, forwarded unchanged.
        service: Request-scoped scope service contract.

    Returns:
        Scope HTTP outputs and native pagination metadata.
    """
    page = await service.list(query)
    output = ScopeOutput.from_objs(page.items)
    return APIResponse[ScopeOutput, PagerMeta](
        success=True,
        data=output,
        meta=PagerMeta.from_total(
            query.page, query.per_page, page.total_items
        ),
    )


@router.get("/{id}", response_model=APIResponse[ScopeOutput, None])
async def get_scope(
    id: IdType,
    service: FromDishka[IScopeService],
) -> APIResponse[ScopeOutput, None]:
    """Read one scope by its native positive database identity.

    Args:
        id: Native validated scope identity.
        service: Request-scoped scope service contract.

    Returns:
        The scope HTTP output in the native response envelope.
    """
    scope = await service.get_by_id(id)
    output = ScopeOutput.from_obj(scope)
    return APIResponse[ScopeOutput, None].from_data(output)


@router.patch("/{id}", response_model=APIResponse[ScopeOutput, None])
async def patch_scope(
    id: IdType,
    data: ScopeUpdate,
    service: FromDishka[IScopeService],
) -> APIResponse[ScopeOutput, None]:
    """Update supplied scope fields while preserving its key.

    Args:
        id: Native validated scope identity.
        data: Validated patch; omission and explicit null remain distinct.
        service: Request-scoped scope service contract.

    Returns:
        The updated scope HTTP output in the native response envelope.
    """
    scope = await service.update(id, data)
    output = ScopeOutput.from_obj(scope)
    return APIResponse[ScopeOutput, None].from_data(output)


@router.delete("/{id}", response_model=APIResponse[ScopeOutput, None])
async def delete_scope(
    id: IdType,
    service: FromDishka[IScopeService],
) -> APIResponse[ScopeOutput, None]:
    """Delete one scope and return its previous state.

    Args:
        id: Native validated scope identity.
        service: Request-scoped scope service contract.

    Returns:
        The removed scope HTTP output in the native response envelope.
    """
    scope = await service.remove(id)
    output = ScopeOutput.from_obj(scope)
    return APIResponse[ScopeOutput, None].from_data(output)

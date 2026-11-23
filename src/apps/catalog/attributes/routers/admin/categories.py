"""Manage the features assigned to each catalog category."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType

from src.apps.catalog.attributes.app.services.categories import BindingService
from src.apps.catalog.attributes.domain.dtos.categories import (
    BindingList,
    BindingSave,
)
from src.apps.catalog.attributes.routers.schemas.categories import (
    BindingDetailOutput,
    BindingOutput,
)
from src.apps.core.auth.routers.dependencies.authorization import require_admin

router = APIRouter(
    prefix="/admin/categories/{category_id:int}/attributes",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("catalog"))],
)


@router.get("")
async def get_bindings(
    category_id: IdType,
    query: Annotated[BindingList, Query()],
    service: FromDishka[BindingService],
) -> APIResponse[BindingDetailOutput, PagerMeta]:
    page = await service.list(category_id, query)
    return APIResponse[BindingDetailOutput, PagerMeta](
        success=True,
        data=BindingDetailOutput.from_objs(page.items),
        meta=PagerMeta.from_total(
            query.page, query.per_page, page.total_items
        ),
    )


@router.put("/{attribute_id:int}")
async def put_binding(
    category_id: IdType,
    attribute_id: IdType,
    data: BindingSave,
    service: FromDishka[BindingService],
) -> APIResponse[BindingOutput, None]:
    binding = await service.save(category_id, attribute_id, data)
    output = BindingOutput.from_obj(binding)
    return APIResponse[BindingOutput, None].from_data(output)


@router.delete("/{attribute_id:int}")
async def delete_binding(
    category_id: IdType,
    attribute_id: IdType,
    service: FromDishka[BindingService],
) -> APIResponse[BindingOutput, None]:
    binding = await service.remove(category_id, attribute_id)
    output = BindingOutput.from_obj(binding)
    return APIResponse[BindingOutput, None].from_data(output)

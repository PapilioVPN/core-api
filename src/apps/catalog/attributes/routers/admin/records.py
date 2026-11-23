"""Manage catalog attribute definitions from the panel."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType

from src.apps.catalog.attributes.app.services.records import AttributeService
from src.apps.catalog.attributes.domain.dtos.records import (
    AttributeCreate,
    AttributeList,
    AttributeUpdate,
)
from src.apps.catalog.attributes.routers.schemas.records import AttributeOutput
from src.apps.core.auth.routers.dependencies.authorization import require_admin

router = APIRouter(
    prefix="/admin/attributes",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("catalog"))],
)


@router.post("", status_code=201)
async def post_attribute(
    data: AttributeCreate, service: FromDishka[AttributeService]
) -> APIResponse[AttributeOutput, None]:
    attribute = await service.create(data)
    output = AttributeOutput.from_obj(attribute)
    return APIResponse[AttributeOutput, None].from_data(output)


@router.get("")
async def get_attributes(
    query: Annotated[AttributeList, Query()],
    service: FromDishka[AttributeService],
) -> APIResponse[AttributeOutput, PagerMeta]:
    page = await service.list(query)
    return APIResponse[AttributeOutput, PagerMeta](
        success=True,
        data=AttributeOutput.from_objs(page.items),
        meta=PagerMeta.from_total(
            query.page, query.per_page, page.total_items
        ),
    )


@router.get("/{id}")
async def get_attribute(
    id: IdType, service: FromDishka[AttributeService]
) -> APIResponse[AttributeOutput, None]:
    attribute = await service.get_by_id(id)
    output = AttributeOutput.from_obj(attribute)
    return APIResponse[AttributeOutput, None].from_data(output)


@router.patch("/{id}")
async def patch_attribute(
    id: IdType,
    data: AttributeUpdate,
    service: FromDishka[AttributeService],
) -> APIResponse[AttributeOutput, None]:
    attribute = await service.update(id, data)
    output = AttributeOutput.from_obj(attribute)
    return APIResponse[AttributeOutput, None].from_data(output)

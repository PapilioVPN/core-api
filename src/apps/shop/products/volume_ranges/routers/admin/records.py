"""Manage a service's custom volume ranges in the panel."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.shop.products.volume_ranges.app.interfaces.commands import (
    IRangeCommand,
)
from src.apps.shop.products.volume_ranges.app.interfaces.services import (
    IRangeCRUD,
)
from src.apps.shop.products.volume_ranges.domain.dtos.records import (
    RangeList,
    RangeWrite,
)
from src.apps.shop.products.volume_ranges.routers.schemas.records import (
    AdminRangeOutput,
)

router = APIRouter(
    prefix="/admin/services/{service_id:int}/volume-ranges",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


@router.post("", status_code=201)
async def post_range(
    service_id: IdType, data: RangeWrite, command: FromDishka[IRangeCommand]
) -> APIResponse[AdminRangeOutput, None]:
    row = await command.create(service_id, data)
    return APIResponse[AdminRangeOutput, None].from_data(
        AdminRangeOutput.from_obj(row)
    )


@router.get("")
async def get_ranges(
    service_id: IdType,
    data: Annotated[RangeList, Query()],
    crud: FromDishka[IRangeCRUD],
) -> APIResponse[AdminRangeOutput, PagerMeta]:
    page = await crud.list(service_id, data)
    return APIResponse[AdminRangeOutput, PagerMeta](
        success=True,
        data=AdminRangeOutput.from_objs(page.items),
        meta=PagerMeta.from_total(data.page, data.per_page, page.total_items),
    )


@router.get("/{id:int}")
async def get_range(
    service_id: IdType, id: IdType, crud: FromDishka[IRangeCRUD]
) -> APIResponse[AdminRangeOutput, None]:
    row = await crud.get_by_id(service_id, id)
    return APIResponse[AdminRangeOutput, None].from_data(
        AdminRangeOutput.from_obj(row)
    )


@router.put("/{id:int}")
async def put_range(
    service_id: IdType,
    id: IdType,
    data: RangeWrite,
    command: FromDishka[IRangeCommand],
) -> APIResponse[AdminRangeOutput, None]:
    row = await command.replace(service_id, id, data)
    return APIResponse[AdminRangeOutput, None].from_data(
        AdminRangeOutput.from_obj(row)
    )


@router.delete("/{id:int}")
async def delete_range(
    service_id: IdType, id: IdType, crud: FromDishka[IRangeCRUD]
) -> APIResponse[AdminRangeOutput, None]:
    row = await crud.remove(service_id, id)
    return APIResponse[AdminRangeOutput, None].from_data(
        AdminRangeOutput.from_obj(row)
    )

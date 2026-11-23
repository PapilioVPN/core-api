"""Register and inspect shop volume definitions."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType, ListIdType

from src.apps.core.auth.routers.dependencies.authorization import require_admin
from src.apps.shop.products.volumes.app.interfaces.services import IVolumeCRUD
from src.apps.shop.products.volumes.domain.dtos.records import (
    VolumeCreate,
    VolumeList,
)
from src.apps.shop.products.volumes.routers.schemas.records import VolumeOutput

router = APIRouter(
    prefix="/admin/volumes",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


@router.post("", status_code=201)
async def post_volume(
    data: VolumeCreate,
    volumes: FromDishka[IVolumeCRUD],
) -> APIResponse[VolumeOutput, None]:
    volume = await volumes.create(data)
    output = VolumeOutput.from_obj(volume)
    return APIResponse[VolumeOutput, None].from_data(output)


@router.get("")
async def get_volumes(
    query: Annotated[VolumeList, Query()],
    volumes: FromDishka[IVolumeCRUD],
) -> APIResponse[VolumeOutput, PagerMeta]:
    page = await volumes.list(query)
    return APIResponse[VolumeOutput, PagerMeta](
        success=True,
        data=VolumeOutput.from_objs(page.items),
        meta=PagerMeta.from_total(
            query.page, query.per_page, page.total_items
        ),
    )


@router.get("/batch")
async def get_volumes_batch(
    ids: Annotated[ListIdType, Query()], volumes: FromDishka[IVolumeCRUD]
) -> APIResponse[VolumeOutput, None]:
    rows = await volumes.get_by_ids(ids)
    return APIResponse[VolumeOutput, None].from_data(
        VolumeOutput.from_objs(rows)
    )


@router.get("/{id:int}")
async def get_volume(
    id: IdType, volumes: FromDishka[IVolumeCRUD]
) -> APIResponse[VolumeOutput, None]:
    volume = await volumes.get_by_id(id)
    output = VolumeOutput.from_obj(volume)
    return APIResponse[VolumeOutput, None].from_data(output)

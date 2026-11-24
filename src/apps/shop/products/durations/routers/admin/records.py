"""Register and inspect reusable shop durations."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType, ListIdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.shop.products.durations.app.interfaces.services import (
    IDurationService,
)
from src.apps.shop.products.durations.domain.dtos.records import (
    DurationCreate,
    DurationList,
)
from src.apps.shop.products.durations.routers.schemas.records import (
    DurationOutput,
)

router = APIRouter(
    prefix="/admin/durations",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


@router.post("", status_code=201)
async def post_duration(
    data: DurationCreate, durations: FromDishka[IDurationService]
) -> APIResponse[DurationOutput, None]:
    duration = await durations.create(data)
    output = DurationOutput.from_obj(duration)
    return APIResponse[DurationOutput, None].from_data(output)


@router.get("")
async def get_durations(
    query: Annotated[DurationList, Query()],
    durations: FromDishka[IDurationService],
) -> APIResponse[DurationOutput, PagerMeta]:
    page = await durations.list(query)
    return APIResponse[DurationOutput, PagerMeta](
        success=True,
        data=DurationOutput.from_objs(page.items),
        meta=PagerMeta.from_total(
            query.page, query.per_page, page.total_items
        ),
    )


@router.get("/batch")
async def get_durations_batch(
    ids: Annotated[ListIdType, Query()],
    durations: FromDishka[IDurationService],
) -> APIResponse[DurationOutput, None]:
    rows = await durations.get_by_ids(ids)
    return APIResponse[DurationOutput, None].from_data(
        DurationOutput.from_objs(rows)
    )


@router.get("/{id:int}")
async def get_duration(
    id: IdType, durations: FromDishka[IDurationService]
) -> APIResponse[DurationOutput, None]:
    duration = await durations.get_by_id(id)
    output = DurationOutput.from_obj(duration)
    return APIResponse[DurationOutput, None].from_data(output)

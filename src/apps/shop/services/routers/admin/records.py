"""Create, inspect and manage services from the shop panel."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType

from src.apps.core.auth.routers.dependencies.authorization import require_admin
from src.apps.shop.services.app.services.records import Services
from src.apps.shop.services.domain.dtos.records import (
    ServiceCreate,
    ServiceList,
    ServiceUpdate,
)
from src.apps.shop.services.routers.schemas.records import ServiceOutput

router = APIRouter(
    prefix="/admin/services",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


@router.post("", status_code=201)
async def post_service(
    data: ServiceCreate, services: FromDishka[Services]
) -> APIResponse[ServiceOutput, None]:
    service = await services.create(data)
    output = ServiceOutput.from_obj(service)
    return APIResponse[ServiceOutput, None].from_data(output)


@router.get("")
async def get_services(
    query: Annotated[ServiceList, Query()],
    services: FromDishka[Services],
) -> APIResponse[ServiceOutput, PagerMeta]:
    page = await services.list(query)
    return APIResponse[ServiceOutput, PagerMeta](
        success=True,
        data=ServiceOutput.from_objs(page.items),
        meta=PagerMeta.from_total(
            query.page, query.per_page, page.total_items
        ),
    )


@router.get("/{id:int}")
async def get_service(
    id: IdType, services: FromDishka[Services]
) -> APIResponse[ServiceOutput, None]:
    service = await services.get_by_id(id)
    output = ServiceOutput.from_obj(service)
    return APIResponse[ServiceOutput, None].from_data(output)


@router.patch("/{id:int}")
async def patch_service(
    id: IdType, data: ServiceUpdate, services: FromDishka[Services]
) -> APIResponse[ServiceOutput, None]:
    service = await services.update(id, data)
    output = ServiceOutput.from_obj(service)
    return APIResponse[ServiceOutput, None].from_data(output)

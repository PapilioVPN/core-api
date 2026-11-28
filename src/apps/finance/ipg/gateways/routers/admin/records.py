"""Manage online payment gateway accounts in the Finance panel."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.commands import IGatewayCreateCommand
from ...app.interfaces.services import IGatewayService
from ...domain.dtos.records import GatewayCreate, GatewayList, GatewayUpdate
from ..schemas.records import GatewayOutput

router = APIRouter(
    prefix="/admin/ipg/gateways",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("finance"))],
)


@router.post("", status_code=201)
async def post_gateway(
    data: GatewayCreate, command: FromDishka[IGatewayCreateCommand]
) -> APIResponse[GatewayOutput, None]:
    gateway = await command.create(data)
    output = GatewayOutput.from_obj(gateway)
    return APIResponse[GatewayOutput, None].from_data(output)


@router.get("")
async def get_gateways(
    query: Annotated[GatewayList, Query()],
    service: FromDishka[IGatewayService],
) -> APIResponse[GatewayOutput, PagerMeta]:
    page = await service.list(query)
    return APIResponse[GatewayOutput, PagerMeta](
        success=True,
        data=GatewayOutput.from_objs(page.items),
        meta=PagerMeta.from_total(
            query.page, query.per_page, page.total_items
        ),
    )


@router.get("/{id:int}")
async def get_gateway(
    id: IdType, service: FromDishka[IGatewayService]
) -> APIResponse[GatewayOutput, None]:
    gateway = await service.get_by_id(id)
    output = GatewayOutput.from_obj(gateway)
    return APIResponse[GatewayOutput, None].from_data(output)


@router.patch("/{id:int}")
async def patch_gateway(
    id: IdType, data: GatewayUpdate, service: FromDishka[IGatewayService]
) -> APIResponse[GatewayOutput, None]:
    gateway = await service.update(id, data)
    output = GatewayOutput.from_obj(gateway)
    return APIResponse[GatewayOutput, None].from_data(output)

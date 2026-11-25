"""Manage gateway accounts from the Shop panel."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType, ListIdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.services import ICryptoGatewayService
from ...domain.dtos.records import GatewayCreate, GatewayList, GatewayUpdate
from ..schemas.records import GatewayOutput

router = APIRouter(
    prefix="/admin/crypto-gateways",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


@router.post("", status_code=201)
async def post_gateway(
    data: GatewayCreate, service: FromDishka[ICryptoGatewayService]
) -> APIResponse[GatewayOutput, None]:
    gateway = await service.create(data)
    return APIResponse[GatewayOutput, None].from_data(
        GatewayOutput.from_obj(gateway)
    )


@router.get("")
async def get_gateways(
    query: Annotated[GatewayList, Query()],
    service: FromDishka[ICryptoGatewayService],
) -> APIResponse[GatewayOutput, PagerMeta]:
    page = await service.list(query)
    return APIResponse[GatewayOutput, PagerMeta](
        success=True,
        data=GatewayOutput.from_objs(page.items),
        meta=PagerMeta.from_total(
            query.page, query.per_page, page.total_items
        ),
    )


@router.get("/batch")
async def get_gateways_batch(
    ids: Annotated[ListIdType, Query()],
    service: FromDishka[ICryptoGatewayService],
) -> APIResponse[GatewayOutput, None]:
    gateways = await service.get_by_ids(ids)
    return APIResponse[GatewayOutput, None].from_data(
        GatewayOutput.from_objs(gateways)
    )


@router.get("/{id:int}")
async def get_gateway(
    id: IdType, service: FromDishka[ICryptoGatewayService]
) -> APIResponse[GatewayOutput, None]:
    gateway = await service.get_by_id(id)
    return APIResponse[GatewayOutput, None].from_data(
        GatewayOutput.from_obj(gateway)
    )


@router.patch("/{id:int}")
async def patch_gateway(
    id: IdType, data: GatewayUpdate, service: FromDishka[ICryptoGatewayService]
) -> APIResponse[GatewayOutput, None]:
    gateway = await service.update(id, data)
    return APIResponse[GatewayOutput, None].from_data(
        GatewayOutput.from_obj(gateway)
    )


@router.delete("/{id:int}")
async def delete_gateway(
    id: IdType, service: FromDishka[ICryptoGatewayService]
) -> APIResponse[GatewayOutput, None]:
    gateway = await service.remove(id)
    return APIResponse[GatewayOutput, None].from_data(
        GatewayOutput.from_obj(gateway)
    )

"""Read or replace one account's configuration from the Shop panel."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.configs import (
    ICryptoGatewayConfigQuery,
    ICryptoGatewayConfigService,
)
from ...domain.dtos.configs import ConfigWrite
from ..schemas.configs import GatewayConfigOutput

router = APIRouter(
    prefix="/admin/crypto-gateways",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


@router.get("/{id:int}/config")
async def get_config(
    id: IdType, query: FromDishka[ICryptoGatewayConfigQuery]
) -> APIResponse[GatewayConfigOutput, None]:
    view = await query.get(id)
    return APIResponse[GatewayConfigOutput, None].from_data(
        GatewayConfigOutput.from_obj(view)
    )


@router.put("/{id:int}/config")
async def put_config(
    id: IdType,
    data: ConfigWrite,
    service: FromDishka[ICryptoGatewayConfigService],
) -> APIResponse[GatewayConfigOutput, None]:
    view = await service.save(id, data)
    return APIResponse[GatewayConfigOutput, None].from_data(
        GatewayConfigOutput.from_obj(view)
    )

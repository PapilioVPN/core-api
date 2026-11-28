"""Read display settings and rotate gateway credentials."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.commands import IGatewayConfigCommand
from ...app.interfaces.queries import IGatewayConfigQuery
from ...domain.dtos.configs import VarizaConfig
from ...domain.enums.records import GatewayKind
from ..schemas.configs import ConfigOutput
from ..schemas.records import GatewayOutput

router = APIRouter(
    prefix="/admin/card-gateways",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("finance"))],
)


@router.get("/{key}/config")
async def get_config(
    key: GatewayKind, query: FromDishka[IGatewayConfigQuery]
) -> APIResponse[ConfigOutput, None]:
    config = await query.get(key)
    output = ConfigOutput.from_obj(config.config | {"key": config.key})
    return APIResponse[ConfigOutput, None].from_data(output)


@router.put("/{id:int}/config")
async def put_config(
    id: IdType, data: VarizaConfig, command: FromDishka[IGatewayConfigCommand]
) -> APIResponse[GatewayOutput, None]:
    gateway = await command.replace(id, data)
    output = GatewayOutput.from_obj(gateway)
    return APIResponse[GatewayOutput, None].from_data(output)

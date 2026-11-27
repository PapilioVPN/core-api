"""Read or replace one account's connection settings from the panel."""

from http import HTTPStatus

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Response
from papilio.api.responses.envelope import APIResponse
from papilio.errors.outputs import BaseErrorOut
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.commands.configs import GatewayConfigCommand
from ...app.interfaces.configs import IGatewayConfigQuery
from ...domain.dtos.configs import ConfigWrite
from ...domain.results.configs import ConfigFailure, GatewayConfigView
from ..schemas.configs import GatewayConfigOutput

router = APIRouter(
    prefix="/admin/crypto-gateways/{id:int}/config",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


def _response(
    response: Response, view: GatewayConfigView | ConfigFailure
) -> APIResponse[GatewayConfigOutput, None]:
    if isinstance(view, ConfigFailure):
        response.status_code = HTTPStatus.SERVICE_UNAVAILABLE
        result = APIResponse[GatewayConfigOutput, None](
            success=False,
            error=BaseErrorOut(
                message="The gateway configuration is unavailable.",
                message_code="crypto_gateway_config_unavailable",
            ),
        )
    else:
        result = APIResponse[GatewayConfigOutput, None].from_data(
            GatewayConfigOutput.from_obj(view)
        )
    return result


@router.get("")
async def get_config(
    id: IdType, response: Response, query: FromDishka[IGatewayConfigQuery]
) -> APIResponse[GatewayConfigOutput, None]:
    view = await query.get(id)
    return _response(response, view)


@router.put("")
async def put_config(
    id: IdType,
    data: ConfigWrite,
    response: Response,
    command: FromDishka[GatewayConfigCommand],
) -> APIResponse[GatewayConfigOutput, None]:
    view = await command.save(id, data)
    return _response(response, view)

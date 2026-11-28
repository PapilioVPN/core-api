"""Accept and track bounded local Start and Stop selections from the Panel."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Response, status
from papilio.api.responses.envelope import APIResponse

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.fleet import (
    IXrayFleetStartCommand,
    IXrayFleetStartQuery,
    IXrayFleetStopCommand,
    IXrayFleetStopQuery,
)
from ...domain.dtos.fleet import (
    XrayFleetStartInput,
    XrayFleetStopInput,
    XrayFleetTrackingInput,
)
from ...domain.results.fleet import XrayFleetOperationResult
from ..dependencies.authorization import require_fleet_read
from ..schemas.fleet import XrayFleetOperationOutput

router = APIRouter(
    prefix="/admin/nodes/xray/instances",
    route_class=DishkaRoute,
)


def _fleet_response(
    results: tuple[XrayFleetOperationResult, ...], response: Response
) -> APIResponse[XrayFleetOperationOutput, None]:
    response.headers["Cache-Control"] = "private, no-store"
    return APIResponse[XrayFleetOperationOutput, None].from_data(
        [XrayFleetOperationOutput.from_result(row) for row in results]
    )


@router.post(
    "/start-operations",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_admin("network"))],
    responses={status.HTTP_200_OK: {"description": "No target was accepted"}},
)
async def start_fleet(
    data: XrayFleetStartInput,
    response: Response,
    command: FromDishka[IXrayFleetStartCommand],
) -> APIResponse[XrayFleetOperationOutput, None]:
    results = await command.start(data)
    if all(row.operation is None for row in results):
        response.status_code = status.HTTP_200_OK
    return _fleet_response(results, response)


@router.post(
    "/start-operations/status", dependencies=[Depends(require_fleet_read)]
)
async def get_fleet_start(
    data: XrayFleetTrackingInput,
    response: Response,
    query: FromDishka[IXrayFleetStartQuery],
) -> APIResponse[XrayFleetOperationOutput, None]:
    results = await query.get(data)
    return _fleet_response(results, response)


@router.post(
    "/stop-operations",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_admin("network"))],
    responses={status.HTTP_200_OK: {"description": "No target was accepted"}},
)
async def stop_fleet(
    data: XrayFleetStopInput,
    response: Response,
    command: FromDishka[IXrayFleetStopCommand],
) -> APIResponse[XrayFleetOperationOutput, None]:
    results = await command.stop(data)
    if all(row.operation is None for row in results):
        response.status_code = status.HTTP_200_OK
    return _fleet_response(results, response)


@router.post(
    "/stop-operations/status", dependencies=[Depends(require_fleet_read)]
)
async def get_fleet_stop(
    data: XrayFleetTrackingInput,
    response: Response,
    query: FromDishka[IXrayFleetStopQuery],
) -> APIResponse[XrayFleetOperationOutput, None]:
    results = await query.get(data)
    return _fleet_response(results, response)

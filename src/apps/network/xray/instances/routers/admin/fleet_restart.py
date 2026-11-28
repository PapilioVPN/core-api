"""Accept and track independent restarts of a saved revision."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Response, status
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.fleet import (
    IXrayFleetRestartCommand,
    IXrayFleetRestartQuery,
)
from ...domain.dtos.fleet import (
    XrayFleetRestartInput,
    XrayFleetTrackingInput,
)
from ..dependencies.authorization import require_fleet_read
from ..schemas.fleet import XrayFleetRestartOutput

router = APIRouter(
    prefix=(
        "/admin/nodes/xray/config-revisions/{revision_id:int}"
        "/restart-operations"
    ),
    route_class=DishkaRoute,
)


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_admin("network"))],
    responses={status.HTTP_200_OK: {"description": "No target was accepted"}},
)
async def restart_fleet(
    revision_id: IdType,
    data: XrayFleetRestartInput,
    response: Response,
    command: FromDishka[IXrayFleetRestartCommand],
) -> APIResponse[XrayFleetRestartOutput, None]:
    results = await command.restart(revision_id, data)
    response.headers["Cache-Control"] = "private, no-store"
    if all(row.operation is None for row in results):
        response.status_code = status.HTTP_200_OK
    return APIResponse[XrayFleetRestartOutput, None].from_data(
        [XrayFleetRestartOutput.from_result(row) for row in results]
    )


@router.post("/status", dependencies=[Depends(require_fleet_read)])
async def get_fleet_restarts(
    revision_id: IdType,
    data: XrayFleetTrackingInput,
    response: Response,
    query: FromDishka[IXrayFleetRestartQuery],
) -> APIResponse[XrayFleetRestartOutput, None]:
    results = await query.get(revision_id, data)
    response.headers["Cache-Control"] = "private, no-store"
    return APIResponse[XrayFleetRestartOutput, None].from_data(
        [XrayFleetRestartOutput.from_result(row) for row in results]
    )

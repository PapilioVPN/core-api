"""Accept and track bounded revision applications across selected targets."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Response, status
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.fleet_apply import (
    IXrayFleetApplyCommand,
    IXrayFleetApplyQuery,
)
from ...domain.dtos.fleet_apply import (
    XrayFleetApplyInput,
    XrayFleetApplyTrackingInput,
)
from ..dependencies.authorization import require_fleet_read
from ..schemas.fleet_apply import XrayFleetApplyOutput

router = APIRouter(
    prefix="/admin/nodes/xray/config-revisions/{revision_id:int}/apply-operations",
    route_class=DishkaRoute,
)


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_admin("network"))],
    responses={status.HTTP_200_OK: {"description": "No target was accepted"}},
)
async def apply_fleet(
    revision_id: IdType,
    data: XrayFleetApplyInput,
    response: Response,
    command: FromDishka[IXrayFleetApplyCommand],
) -> APIResponse[XrayFleetApplyOutput, None]:
    results = await command.apply(revision_id, data)
    response.headers["Cache-Control"] = "private, no-store"
    if all(row.operation is None for row in results):
        response.status_code = status.HTTP_200_OK
    return APIResponse[XrayFleetApplyOutput, None].from_data(
        [XrayFleetApplyOutput.from_result(row) for row in results]
    )


@router.post("/status", dependencies=[Depends(require_fleet_read)])
async def get_fleet_apply(
    revision_id: IdType,
    data: XrayFleetApplyTrackingInput,
    response: Response,
    query: FromDishka[IXrayFleetApplyQuery],
) -> APIResponse[XrayFleetApplyOutput, None]:
    response.headers["Cache-Control"] = "private, no-store"
    results = await query.get(revision_id, data)
    return APIResponse[XrayFleetApplyOutput, None].from_data(
        [XrayFleetApplyOutput.from_result(row) for row in results]
    )

"""Read a bounded set of live Xray targets without requesting any mutation."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Response
from papilio.api.responses.envelope import APIResponse

from ...app.interfaces.status import IXrayFleetStatusQuery
from ...domain.dtos.fleet_status import XrayFleetStatusInput
from ..dependencies.authorization import require_fleet_read
from ..schemas.status import XrayStatusOutput

router = APIRouter(
    prefix="/admin/nodes/xray/instances",
    route_class=DishkaRoute,
    dependencies=[Depends(require_fleet_read)],
)


@router.post("/status")
async def get_fleet_status(
    data: XrayFleetStatusInput,
    response: Response,
    query: FromDishka[IXrayFleetStatusQuery],
) -> APIResponse[XrayStatusOutput, None]:
    response.headers["Cache-Control"] = "private, no-store"
    results = await query.get(data)
    return APIResponse[XrayStatusOutput, None].from_data(
        [
            XrayStatusOutput.from_result(
                row.node_id, row.instance_id, row.result
            )
            for row in results
        ]
    )

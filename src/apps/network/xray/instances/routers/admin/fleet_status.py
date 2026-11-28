"""Read a bounded set of live Xray targets without requesting any mutation."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Response
from papilio.api.responses.envelope import APIResponse

from src.apps.core.access.auth.app.validators.authorization import (
    validate_admin_permission,
)
from src.apps.core.access.auth.domain.enums.permissions import AdminPermission
from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.auth.routers.dependencies.identity import (
    current_admin,
)

from ...app.interfaces.status import IXrayFleetStatusQuery
from ...domain.dtos.fleet_status import XrayFleetStatusInput
from ..schemas.status import XrayStatusOutput


async def _require_read(
    identity: Annotated[AdminIdentity, Depends(current_admin)],
) -> None:
    validate_admin_permission(identity, "network", AdminPermission.READ)


router = APIRouter(
    prefix="/admin/nodes/xray/instances",
    route_class=DishkaRoute,
    dependencies=[Depends(_require_read)],
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

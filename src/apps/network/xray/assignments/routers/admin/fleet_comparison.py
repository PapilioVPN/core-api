"""Expose the read-only live fleet comparison to authorized Panel operators."""

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

from ...app.interfaces.fleet_comparison import IXrayFleetComparisonQuery
from ...domain.dtos.fleet_comparison import XrayFleetComparisonInput
from ..schemas.records import XrayRevisionComparisonOutput


async def _require_read(
    identity: Annotated[AdminIdentity, Depends(current_admin)],
) -> None:
    validate_admin_permission(identity, "network", AdminPermission.READ)


router = APIRouter(
    prefix="/admin/nodes/xray/instances/desired-revision",
    route_class=DishkaRoute,
    dependencies=[Depends(_require_read)],
)


@router.post("/comparison")
async def compare_desired_revisions(
    data: XrayFleetComparisonInput,
    response: Response,
    query: FromDishka[IXrayFleetComparisonQuery],
) -> APIResponse[XrayRevisionComparisonOutput, None]:
    results = await query.get(data)
    response.headers["Cache-Control"] = "private, no-store"
    return APIResponse[XrayRevisionComparisonOutput, None].from_data(
        [
            XrayRevisionComparisonOutput.from_comparison(
                row.node_id, row.instance_id, row.comparison
            )
            for row in results
        ]
    )

"""Read a registered node's current host stats for the admin panel."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Response
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.app.validators.authorization import (
    validate_admin_permission,
)
from src.apps.core.access.auth.domain.enums.permissions import AdminPermission
from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.core.access.auth.routers.dependencies.identity import (
    current_admin,
)

from ...app.interfaces.host import IFleetHostStatsQuery, IHostStatsQuery
from ...domain.dtos.host import FleetHostStatsInput
from ..schemas.host import NodeHostOutput

router = APIRouter(
    prefix="/admin/nodes",
    route_class=DishkaRoute,
)


async def _require_read(
    identity: Annotated[AdminIdentity, Depends(current_admin)],
) -> None:
    validate_admin_permission(identity, "network", AdminPermission.READ)


@router.get(
    "/{id:int}/host-stats", dependencies=[Depends(require_admin("network"))]
)
async def get_host_stats(
    id: IdType, hosts: FromDishka[IHostStatsQuery]
) -> APIResponse[NodeHostOutput, None]:
    result = await hosts.get(id)
    return APIResponse[NodeHostOutput, None].from_data(
        NodeHostOutput.from_result(id, result)
    )


@router.post("/host-stats", dependencies=[Depends(_require_read)])
async def get_fleet_host_stats(
    data: FleetHostStatsInput,
    response: Response,
    hosts: FromDishka[IFleetHostStatsQuery],
) -> APIResponse[NodeHostOutput, None]:
    results = await hosts.get(data)
    response.headers["Cache-Control"] = "private, no-store"
    return APIResponse[NodeHostOutput, None].from_data(
        [
            NodeHostOutput.from_result(row.node_id, row.observation)
            for row in results
        ]
    )

"""Read a registered node's current host stats for the admin panel."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.host import IHostStatsQuery
from ..schemas.host import HostStatsOutput, NodeHostOutput

router = APIRouter(
    prefix="/admin/nodes/{id:int}/host-stats",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)


@router.get("")
async def get_host_stats(
    id: IdType, hosts: FromDishka[IHostStatsQuery]
) -> APIResponse[NodeHostOutput, None]:
    result = await hosts.get(id)
    stats = HostStatsOutput.from_obj(result.stats) if result.stats else None
    output = NodeHostOutput(
        node_id=id,
        status=result.status,
        stats=stats,
        received_at=result.received_at,
    )
    return APIResponse[NodeHostOutput, None].from_data(output)

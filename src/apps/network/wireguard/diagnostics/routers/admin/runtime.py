"""Expose WireGuardRuntime to authorized Panel operators."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Response
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.network.wireguard.interfaces.domain.dtos.identity import (
    WireGuardInterfaceName,
)

from ...app.interfaces.runtime import IWireGuardRuntimeQuery
from ..schemas.runtime import (
    WireGuardRuntimeObservationOutput,
    WireGuardRuntimeOutput,
)

router = APIRouter(
    prefix="/admin/nodes/{node_id:int}/wireguard/interfaces/{name}",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)


@router.get("/runtime-stats")
async def get_runtime(
    node_id: IdType,
    name: WireGuardInterfaceName,
    response: Response,
    query: FromDishka[IWireGuardRuntimeQuery],
) -> APIResponse[WireGuardRuntimeObservationOutput, None]:
    result = await query.get(node_id, name)
    response.headers["Cache-Control"] = "private, no-store"
    output = WireGuardRuntimeObservationOutput(
        node_id=node_id,
        name=name,
        status=result.status,
        received_at=result.received_at,
        runtime=WireGuardRuntimeOutput.from_obj(result.value)
        if result.value is not None
        else None,
    )
    return APIResponse[WireGuardRuntimeObservationOutput, None].from_data(
        output
    )

"""Expose WireGuardEgress to authorized Panel operators."""

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

from ...app.interfaces.egress import IWireGuardEgressQuery
from ..schemas.egress import (
    WireGuardEgressObservationOutput,
    WireGuardEgressOutput,
)

router = APIRouter(
    prefix="/admin/nodes/{node_id:int}/wireguard/interfaces/{name}",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)


@router.get("/egress-probe")
async def get_egress(
    node_id: IdType,
    name: WireGuardInterfaceName,
    response: Response,
    query: FromDishka[IWireGuardEgressQuery],
) -> APIResponse[WireGuardEgressObservationOutput, None]:
    result = await query.get(node_id, name)
    response.headers["Cache-Control"] = "private, no-store"
    output = WireGuardEgressObservationOutput(
        node_id=node_id,
        name=name,
        status=result.status,
        received_at=result.received_at,
        egress=WireGuardEgressOutput.from_obj(result.value)
        if result.value is not None
        else None,
    )
    return APIResponse[WireGuardEgressObservationOutput, None].from_data(
        output
    )

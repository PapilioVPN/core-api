"""Expose WireGuard status to authorized Panel operators."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.network.wireguard.interfaces.domain.dtos.identity import (
    WireGuardInterfaceName,
)

from ...app.interfaces.status import IWireGuardStatusQuery
from ..schemas.status import (
    WireGuardStatusObservationOutput,
    WireGuardStatusOutput,
)

router = APIRouter(
    prefix="/admin/nodes/{node_id:int}/wireguard/interfaces/{name}",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)


@router.get("")
async def get_status(
    node_id: IdType,
    name: WireGuardInterfaceName,
    query: FromDishka[IWireGuardStatusQuery],
) -> APIResponse[WireGuardStatusObservationOutput, None]:
    result = await query.get(node_id, name)
    output = WireGuardStatusObservationOutput(
        node_id=node_id,
        name=name,
        status=result.status,
        interface=WireGuardStatusOutput.from_obj(result.value)
        if result.value is not None
        else None,
        received_at=result.received_at,
    )
    return APIResponse[WireGuardStatusObservationOutput, None].from_data(
        output
    )

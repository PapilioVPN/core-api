"""Expose one WireGuard membership observation to the Panel."""

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

from ...app.interfaces.membership import IWireGuardMembershipQuery
from ..schemas.membership import WireGuardMembershipOutput, WireGuardPeerOutput

router = APIRouter(
    prefix="/admin/nodes/{node_id:int}/wireguard/interfaces/{name}/peers",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)


@router.get("")
async def get_peers(
    node_id: IdType,
    name: WireGuardInterfaceName,
    response: Response,
    query: FromDishka[IWireGuardMembershipQuery],
) -> APIResponse[WireGuardMembershipOutput, None]:
    result = await query.get(node_id, name)
    response.headers["Cache-Control"] = "private, no-store"
    output = WireGuardMembershipOutput(
        node_id=node_id,
        name=name,
        status=result.status,
        received_at=result.received_at,
        peers=WireGuardPeerOutput.from_objs(result.value)
        if result.value is not None
        else None,
    )
    return APIResponse[WireGuardMembershipOutput, None].from_data(output)

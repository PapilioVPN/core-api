"""Expose Hysteria status to authorized Panel operators."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.network.nodes.connections.domain.dtos.identity import (
    NodeInstanceID,
)

from ...app.interfaces.status import IHysteriaStatusQuery
from ..schemas.status import (
    HysteriaStatusObservationOutput,
    HysteriaStatusOutput,
)

router = APIRouter(
    prefix="/admin/nodes/{node_id:int}/hysteria/instances/{instance_id}",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)


@router.get("")
async def get_status(
    node_id: IdType,
    instance_id: NodeInstanceID,
    query: FromDishka[IHysteriaStatusQuery],
) -> APIResponse[HysteriaStatusObservationOutput, None]:
    result = await query.get(node_id, instance_id)
    output = HysteriaStatusObservationOutput(
        node_id=node_id,
        instance_id=instance_id,
        status=result.status,
        instance=HysteriaStatusOutput.from_obj(result.value)
        if result.value is not None
        else None,
        received_at=result.received_at,
    )
    return APIResponse[HysteriaStatusObservationOutput, None].from_data(output)

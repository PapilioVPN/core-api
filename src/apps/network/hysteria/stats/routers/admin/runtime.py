"""Expose HysteriaRuntime to authorized Panel operators."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Response
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.network.nodes.connections.domain.dtos.identity import (
    NodeInstanceID,
)

from ...app.interfaces.runtime import IHysteriaRuntimeQuery
from ..schemas.runtime import (
    HysteriaRuntimeObservationOutput,
    HysteriaRuntimeOutput,
)

router = APIRouter(
    prefix="/admin/nodes/{node_id:int}/hysteria/instances/{instance_id}",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)


@router.get("/runtime-stats")
async def get_runtime(
    node_id: IdType,
    instance_id: NodeInstanceID,
    response: Response,
    query: FromDishka[IHysteriaRuntimeQuery],
) -> APIResponse[HysteriaRuntimeObservationOutput, None]:
    result = await query.get(node_id, instance_id)
    response.headers["Cache-Control"] = "private, no-store"
    output = HysteriaRuntimeObservationOutput(
        node_id=node_id,
        instance_id=instance_id,
        status=result.status,
        received_at=result.received_at,
        runtime=HysteriaRuntimeOutput.from_obj(result.value)
        if result.value is not None
        else None,
    )
    return APIResponse[HysteriaRuntimeObservationOutput, None].from_data(
        output
    )

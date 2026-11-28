"""Expose live Xray outbound health to authorized operators."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.network.xray.instances.domain.dtos.identity import XrayInstanceID

from ...app.interfaces.health import IXrayOutboundHealthQuery
from ...domain.dtos.health import XrayOutboundTag
from ..schemas.health import (
    XrayOutboundObservationOutput,
    XrayOutboundSampleOutput,
)

router = APIRouter(
    prefix="/admin/nodes/{node_id:int}/xray/instances/{instance_id}",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)


@router.get("/outbound-health")
async def get_outbound_health(
    node_id: IdType,
    instance_id: XrayInstanceID,
    query: FromDishka[IXrayOutboundHealthQuery],
    tag: Annotated[XrayOutboundTag | None, Query()] = None,
) -> APIResponse[XrayOutboundObservationOutput, None]:
    result = await query.get(node_id, instance_id, tag)
    output = XrayOutboundObservationOutput(
        node_id=node_id,
        instance_id=instance_id,
        status=result.status,
        observations=[
            XrayOutboundSampleOutput.from_obj(sample)
            for sample in result.value
        ]
        if result.value is not None
        else None,
        received_at=result.received_at,
    )
    return APIResponse[XrayOutboundObservationOutput, None].from_data(output)

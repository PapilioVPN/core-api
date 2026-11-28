"""Expose live named VLESS membership count to Network operators."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query, Response
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.network.xray.instances.domain.dtos.identity import XrayInstanceID

from ...app.interfaces.count import IXrayVlessCountQuery
from ...domain.dtos.identity import XrayInboundTag
from ..schemas.count import XrayVlessCountOutput

router = APIRouter(
    prefix="/admin/nodes/{node_id:int}/xray/instances/{instance_id}/accounts",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)


@router.get("/vless/count")
async def get_vless_count(
    node_id: IdType,
    instance_id: XrayInstanceID,
    inbound_tag: Annotated[XrayInboundTag, Query()],
    response: Response,
    query: FromDishka[IXrayVlessCountQuery],
) -> APIResponse[XrayVlessCountOutput, None]:
    response.headers["Cache-Control"] = "private, no-store"
    result = await query.get(node_id, instance_id, inbound_tag)
    output = XrayVlessCountOutput(
        node_id=node_id,
        instance_id=instance_id,
        inbound_tag=inbound_tag,
        count=result.value,
        status=result.status,
        received_at=result.received_at,
    )
    return APIResponse[XrayVlessCountOutput, None].from_data(output)

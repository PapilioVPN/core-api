"""Expose live Xray traffic for authorized Network operators."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.network.xray.instances.domain.dtos.identity import XrayInstanceID

from ...app.interfaces.traffic import IXrayTrafficQuery
from ...domain.dtos.traffic import XrayCounterName
from ...domain.enums.traffic import XrayTrafficScope
from ..schemas.traffic import (
    XrayTrafficCounterOutput,
    XrayTrafficListOutput,
    XrayTrafficOutput,
)

router = APIRouter(
    prefix="/admin/nodes/{node_id:int}/xray/instances/{instance_id}/traffic",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)


@router.get("/{scope}/counter")
async def get_traffic_counter(
    node_id: IdType,
    instance_id: XrayInstanceID,
    scope: XrayTrafficScope,
    name: Annotated[XrayCounterName, Query()],
    query: FromDishka[IXrayTrafficQuery],
) -> APIResponse[XrayTrafficCounterOutput, None]:
    result = await query.get(node_id, instance_id, scope, name)
    output = XrayTrafficCounterOutput(
        node_id=node_id,
        instance_id=instance_id,
        scope=scope,
        status=result.status,
        received_at=result.received_at,
        counter=XrayTrafficOutput.from_obj(result.value)
        if result.value is not None
        else None,
    )
    return APIResponse[XrayTrafficCounterOutput, None].from_data(output)


@router.get("/{scope}")
async def list_traffic(
    node_id: IdType,
    instance_id: XrayInstanceID,
    scope: XrayTrafficScope,
    query: FromDishka[IXrayTrafficQuery],
) -> APIResponse[XrayTrafficListOutput, None]:
    result = await query.list(node_id, instance_id, scope)
    output = XrayTrafficListOutput(
        node_id=node_id,
        instance_id=instance_id,
        scope=scope,
        status=result.status,
        received_at=result.received_at,
        entries=[XrayTrafficOutput.from_obj(entry) for entry in result.value]
        if result.value is not None
        else None,
    )
    return APIResponse[XrayTrafficListOutput, None].from_data(output)

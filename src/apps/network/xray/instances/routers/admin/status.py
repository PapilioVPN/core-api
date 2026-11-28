"""Read one registered node's Xray instance status."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.status import IXrayStatusQuery
from ...domain.dtos.identity import XrayInstanceID
from ..schemas.status import XrayStatusOutput

router = APIRouter(
    prefix="/admin/nodes/{node_id:int}/xray/instances",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)


@router.get("/{instance_id}")
async def get_status(
    node_id: IdType,
    instance_id: XrayInstanceID,
    query: FromDishka[IXrayStatusQuery],
) -> APIResponse[XrayStatusOutput, None]:
    result = await query.get(node_id, instance_id)
    output = XrayStatusOutput.from_result(node_id, instance_id, result)
    return APIResponse[XrayStatusOutput, None].from_data(output)

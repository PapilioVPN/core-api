"""Accept and track configured starts on registered Node instances."""

from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Header, status
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.start import IXrayStartCommand, IXrayStartQuery
from ...domain.dtos.instances import XrayInstanceID
from ..schemas.start import XrayStartOutput

router = APIRouter(
    prefix="/admin/nodes/{node_id:int}/xray/instances/{instance_id}/start-operations",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def start_instance(
    node_id: IdType,
    instance_id: XrayInstanceID,
    request_key: Annotated[UUID, Header(alias="Idempotency-Key")],
    command: FromDishka[IXrayStartCommand],
) -> APIResponse[XrayStartOutput, None]:
    operation = await command.submit(node_id, instance_id, request_key)
    return APIResponse[XrayStartOutput, None].from_data(
        XrayStartOutput.from_obj(operation)
    )


@router.get("/{id:int}")
async def get_start_operation(
    node_id: IdType,
    instance_id: XrayInstanceID,
    id: IdType,
    query: FromDishka[IXrayStartQuery],
) -> APIResponse[XrayStartOutput, None]:
    operation = await query.get(node_id, instance_id, id)
    return APIResponse[XrayStartOutput, None].from_data(
        XrayStartOutput.from_obj(operation)
    )

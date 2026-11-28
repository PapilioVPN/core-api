"""Accept and track one saved revision on a registered Xray instance."""

from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Header, status
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.apply import IXrayApplyCommand
from ...app.interfaces.start import IXrayStartQuery
from ...domain.dtos.identity import XrayInstanceID
from ..schemas.apply import XrayApplyOutput

router = APIRouter(
    prefix=(
        "/admin/nodes/{node_id:int}/xray/instances/{instance_id}"
        "/config-revisions/{revision_id:int}/apply-operations"
    ),
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def apply_revision(
    node_id: IdType,
    instance_id: XrayInstanceID,
    revision_id: IdType,
    request_key: Annotated[UUID, Header(alias="Idempotency-Key")],
    command: FromDishka[IXrayApplyCommand],
) -> APIResponse[XrayApplyOutput, None]:
    operation = await command.apply(
        node_id, instance_id, revision_id, request_key
    )
    return APIResponse[XrayApplyOutput, None].from_data(
        XrayApplyOutput.from_obj(operation)
    )


@router.get("/{id:int}")
async def get_apply_operation(
    node_id: IdType,
    instance_id: XrayInstanceID,
    revision_id: IdType,
    id: IdType,
    query: FromDishka[IXrayStartQuery],
) -> APIResponse[XrayApplyOutput, None]:
    operation = await query.get(
        node_id, instance_id, id, revision_id=revision_id
    )
    return APIResponse[XrayApplyOutput, None].from_data(
        XrayApplyOutput.from_obj(operation)
    )

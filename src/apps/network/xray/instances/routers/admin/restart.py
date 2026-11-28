"""Accept and track a forced restart with one saved Xray revision."""

from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Header, status
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.restart import IXrayRestartCommand
from ...app.interfaces.start import IXrayStartQuery
from ...domain.dtos.identity import XrayInstanceID
from ...domain.enums.start import XrayExecutionAction
from ..schemas.restart import XrayRestartOutput

router = APIRouter(
    prefix=(
        "/admin/nodes/{node_id:int}/xray/instances/{instance_id}"
        "/config-revisions/{revision_id:int}/restart-operations"
    ),
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def restart_instance(
    node_id: IdType,
    instance_id: XrayInstanceID,
    revision_id: IdType,
    request_key: Annotated[UUID, Header(alias="Idempotency-Key")],
    command: FromDishka[IXrayRestartCommand],
) -> APIResponse[XrayRestartOutput, None]:
    operation = await command.restart(
        node_id, instance_id, revision_id, request_key
    )
    return APIResponse[XrayRestartOutput, None].from_data(
        XrayRestartOutput.from_obj(operation)
    )


@router.get("/{id:int}")
async def get_restart_operation(
    node_id: IdType,
    instance_id: XrayInstanceID,
    revision_id: IdType,
    id: IdType,
    query: FromDishka[IXrayStartQuery],
) -> APIResponse[XrayRestartOutput, None]:
    operation = await query.get(
        node_id,
        instance_id,
        id,
        revision_id=revision_id,
        action=XrayExecutionAction.RESTART,
    )
    return APIResponse[XrayRestartOutput, None].from_data(
        XrayRestartOutput.from_obj(operation)
    )

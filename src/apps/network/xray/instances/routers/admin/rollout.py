"""Submit a rolling Xray restart and poll its persisted evidence."""

from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Header, Response, status
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.rollout import (
    IRestartRolloutAdmission,
    IRestartRolloutQuery,
)
from ...domain.dtos.rollout import RestartRolloutInput
from ..schemas.rollout import RestartRolloutOutput

router = APIRouter(
    prefix="/admin/nodes/xray/config-revisions/{revision_id:int}/restart-rollouts",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def submit_restart_rollout(
    revision_id: IdType,
    data: RestartRolloutInput,
    response: Response,
    request_key: Annotated[UUID, Header(alias="Idempotency-Key")],
    command: FromDishka[IRestartRolloutAdmission],
) -> APIResponse[RestartRolloutOutput, None]:
    snapshot = await command.submit(revision_id, request_key, data)
    response.headers["Cache-Control"] = "private, no-store"
    return APIResponse[RestartRolloutOutput, None].from_data(
        RestartRolloutOutput.from_snapshot(snapshot)
    )


@router.get("/{id:int}")
async def get_restart_rollout(
    revision_id: IdType,
    id: IdType,
    response: Response,
    query: FromDishka[IRestartRolloutQuery],
) -> APIResponse[RestartRolloutOutput, None]:
    snapshot = await query.get(revision_id, id)
    response.headers["Cache-Control"] = "private, no-store"
    return APIResponse[RestartRolloutOutput, None].from_data(
        RestartRolloutOutput.from_snapshot(snapshot)
    )

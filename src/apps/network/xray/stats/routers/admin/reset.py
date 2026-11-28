"""Admit authorized resets and read their durable status from the Panel."""

from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Header, Response, status
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.app.validators.authorization import (
    validate_admin_permission,
)
from src.apps.core.access.auth.domain.enums.permissions import AdminPermission
from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.core.access.auth.routers.dependencies.identity import (
    current_admin,
)
from src.apps.network.xray.instances.domain.dtos.identity import XrayInstanceID

from ...app.interfaces.reset import IXrayTrafficResets
from ...domain.dtos.reset import (
    CounterResetInput,
    PairResetInput,
    ScopeResetInput,
)
from ...domain.enums.reset import ResetKind
from ...domain.enums.traffic import XrayTrafficScope
from ...domain.results.reset import ResetSelection
from ..schemas.reset import TrafficResetOutput


async def _authorize_reset(
    identity: Annotated[AdminIdentity, Depends(current_admin)],
) -> None:
    validate_admin_permission(identity, "network", AdminPermission.UPDATE)


router = APIRouter(
    prefix="/admin/nodes/{node_id:int}/xray/instances/{instance_id}/traffic",
    route_class=DishkaRoute,
)

type ResetRequestKey = Annotated[UUID, Header(alias="Idempotency-Key")]


@router.post(
    "/{scope}/resets/counter",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(_authorize_reset)],
)
async def reset_counter(
    node_id: IdType,
    instance_id: XrayInstanceID,
    scope: XrayTrafficScope,
    data: CounterResetInput,
    key: ResetRequestKey,
    service: FromDishka[IXrayTrafficResets],
) -> APIResponse[TrafficResetOutput, None]:
    selection = ResetSelection(
        scope, ResetKind.COUNTER, data.name, data.direction
    )
    result = await service.submit(node_id, instance_id, key, selection)
    return APIResponse[TrafficResetOutput, None].from_data(
        TrafficResetOutput.from_reset(result)
    )


@router.post(
    "/{scope}/resets/pair",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(_authorize_reset)],
)
async def reset_pair(
    node_id: IdType,
    instance_id: XrayInstanceID,
    scope: XrayTrafficScope,
    data: PairResetInput,
    key: ResetRequestKey,
    service: FromDishka[IXrayTrafficResets],
) -> APIResponse[TrafficResetOutput, None]:
    selection = ResetSelection(scope, ResetKind.PAIR, data.name)
    result = await service.submit(node_id, instance_id, key, selection)
    return APIResponse[TrafficResetOutput, None].from_data(
        TrafficResetOutput.from_reset(result)
    )


@router.post(
    "/{scope}/resets/scope",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(_authorize_reset)],
)
async def reset_scope(
    node_id: IdType,
    instance_id: XrayInstanceID,
    scope: XrayTrafficScope,
    data: ScopeResetInput,
    key: ResetRequestKey,
    service: FromDishka[IXrayTrafficResets],
) -> APIResponse[TrafficResetOutput, None]:
    selection = ResetSelection(
        scope, ResetKind.SCOPE, max_counters=data.max_counters
    )
    result = await service.submit(node_id, instance_id, key, selection)
    return APIResponse[TrafficResetOutput, None].from_data(
        TrafficResetOutput.from_reset(result)
    )


@router.get(
    "/resets/{id:int}", dependencies=[Depends(require_admin("network"))]
)
async def get_reset(
    node_id: IdType,
    instance_id: XrayInstanceID,
    id: IdType,
    response: Response,
    service: FromDishka[IXrayTrafficResets],
) -> APIResponse[TrafficResetOutput, None]:
    response.headers["Cache-Control"] = "private, no-store"
    result = await service.get(node_id, instance_id, id)
    return APIResponse[TrafficResetOutput, None].from_data(
        TrafficResetOutput.from_reset(result)
    )

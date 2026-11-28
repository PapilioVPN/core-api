"""Expose WireGuard dry run to authorized Panel operators."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.network.wireguard.interfaces.domain.dtos.identity import (
    WireGuardInterfaceName,
)

from ...app.interfaces.dry_run import IWireGuardValidationService
from ...domain.dtos.dry_run import WireGuardCandidate
from ..schemas.dry_run import (
    WireGuardValidationObservationOutput,
    WireGuardValidationOutput,
)

router = APIRouter(
    prefix="/admin/nodes/{node_id:int}/wireguard/interfaces/{name}",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)


@router.post("/config-validations")
async def validate_config(
    node_id: IdType,
    name: WireGuardInterfaceName,
    data: WireGuardCandidate,
    validation: FromDishka[IWireGuardValidationService],
) -> APIResponse[WireGuardValidationObservationOutput, None]:
    result = await validation.validate(node_id, name, data)
    output = WireGuardValidationObservationOutput(
        node_id=node_id,
        name=name,
        status=result.status,
        validation=WireGuardValidationOutput.from_obj(result.value)
        if result.value is not None
        else None,
        received_at=result.received_at,
    )
    return APIResponse[WireGuardValidationObservationOutput, None].from_data(
        output
    )

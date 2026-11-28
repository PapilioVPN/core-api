"""Expose OpenVPN dry run to authorized Panel operators."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.network.nodes.connections.domain.dtos.identity import (
    NodeInstanceID,
)

from ...app.interfaces.dry_run import IOpenVPNValidationService
from ...domain.dtos.dry_run import OpenVPNCandidate
from ..schemas.dry_run import (
    OpenVPNValidationObservationOutput,
    OpenVPNValidationOutput,
)

router = APIRouter(
    prefix="/admin/nodes/{node_id:int}/openvpn/instances/{instance_id}",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)


@router.post("/config-validations")
async def validate_config(
    node_id: IdType,
    instance_id: NodeInstanceID,
    data: OpenVPNCandidate,
    validation: FromDishka[IOpenVPNValidationService],
) -> APIResponse[OpenVPNValidationObservationOutput, None]:
    result = await validation.validate(node_id, instance_id, data)
    output = OpenVPNValidationObservationOutput(
        node_id=node_id,
        instance_id=instance_id,
        status=result.status,
        validation=OpenVPNValidationOutput.from_obj(result.value)
        if result.value is not None
        else None,
        received_at=result.received_at,
    )
    return APIResponse[OpenVPNValidationObservationOutput, None].from_data(
        output
    )

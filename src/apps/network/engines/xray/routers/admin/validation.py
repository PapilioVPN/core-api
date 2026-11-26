"""Validate a proposed Xray configuration from the Panel."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.validation import IXrayConfigValidation
from ...domain.dtos.instances import XrayInstanceID
from ...domain.dtos.validation import XrayConfigCandidate
from ..schemas.validation import (
    XrayConfigValidationOutput,
    XrayRevisionValidationOutput,
)

router = APIRouter(
    prefix="/admin/nodes/{node_id:int}/xray/instances",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)


@router.post("/{instance_id}/config-validations")
async def validate_config(
    node_id: IdType,
    instance_id: XrayInstanceID,
    data: XrayConfigCandidate,
    validation: FromDishka[IXrayConfigValidation],
) -> APIResponse[XrayConfigValidationOutput, None]:
    result = await validation.validate(node_id, instance_id, data)
    output = XrayConfigValidationOutput.from_obj(result)
    return APIResponse[XrayConfigValidationOutput, None].from_data(output)


@router.post("/{instance_id}/config-revisions/{revision_id:int}/validations")
async def validate_revision(
    node_id: IdType,
    instance_id: XrayInstanceID,
    revision_id: IdType,
    validation: FromDishka[IXrayConfigValidation],
) -> APIResponse[XrayRevisionValidationOutput, None]:
    result = await validation.validate_revision(
        node_id, instance_id, revision_id
    )
    output = XrayRevisionValidationOutput(
        revision_id=revision_id,
        validation=XrayConfigValidationOutput.from_obj(result),
    )
    return APIResponse[XrayRevisionValidationOutput, None].from_data(output)

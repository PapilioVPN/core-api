"""Validate a proposed Xray configuration from the Panel."""

from http import HTTPStatus

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Response
from papilio.api.responses.envelope import APIResponse
from papilio.errors.outputs import BaseErrorOut
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.network.xray.instances.domain.dtos.identity import XrayInstanceID
from src.apps.network.xray.revisions.domain.dtos.source import (
    XrayConfigCandidate,
)

from ...app.interfaces.dry_run import IXrayConfigValidation
from ..schemas.dry_run import (
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
    response: Response,
    validation: FromDishka[IXrayConfigValidation],
) -> APIResponse[XrayRevisionValidationOutput, None]:
    result = await validation.validate_revision(
        node_id, instance_id, revision_id
    )
    if result is None:
        response.status_code = HTTPStatus.SERVICE_UNAVAILABLE
        body = APIResponse[XrayRevisionValidationOutput, None](
            success=False,
            error=BaseErrorOut(
                message="The Xray revision source is unavailable.",
                message_code="xray_revision_source_unavailable",
            ),
        )
    else:
        output = XrayRevisionValidationOutput(
            revision_id=revision_id,
            validation=XrayConfigValidationOutput.from_obj(result),
        )
        body = APIResponse[XrayRevisionValidationOutput, None].from_data(
            output
        )
    return body

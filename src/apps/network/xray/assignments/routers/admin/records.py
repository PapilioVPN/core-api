"""Manage one desired revision and show its on-demand runtime comparison."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Response, status
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.network.xray.instances.domain.dtos.identity import XrayInstanceID

from ...app.interfaces.records import (
    IXrayAssignmentQuery,
    IXrayAssignmentService,
    IXrayRevisionComparisonQuery,
)
from ...domain.dtos.records import AssignXrayRevision
from ..schemas.records import (
    XrayAssignmentOutput,
    XrayDesiredRevisionOutput,
    XrayRevisionComparisonOutput,
)

router = APIRouter(
    prefix="/admin/nodes/{node_id:int}/xray/instances/{instance_id}/desired-revision",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)


@router.get("")
async def get_desired_revision(
    node_id: IdType,
    instance_id: XrayInstanceID,
    response: Response,
    query: FromDishka[IXrayAssignmentQuery],
) -> APIResponse[XrayAssignmentOutput, None]:
    selected = await query.get(node_id, instance_id)
    response.headers["Cache-Control"] = "private, no-store"
    return APIResponse[XrayAssignmentOutput, None].from_data(
        XrayAssignmentOutput(
            node_id=node_id,
            instance_id=instance_id,
            desired=XrayDesiredRevisionOutput.from_obj(selected.desired)
            if selected.desired is not None
            else None,
        )
    )


@router.put("")
async def set_desired_revision(
    node_id: IdType,
    instance_id: XrayInstanceID,
    data: AssignXrayRevision,
    response: Response,
    service: FromDishka[IXrayAssignmentService],
) -> APIResponse[XrayAssignmentOutput, None]:
    desired = await service.set(node_id, instance_id, data.revision_id)
    response.headers["Cache-Control"] = "private, no-store"
    return APIResponse[XrayAssignmentOutput, None].from_data(
        XrayAssignmentOutput(
            node_id=node_id,
            instance_id=instance_id,
            desired=XrayDesiredRevisionOutput.from_obj(desired),
        )
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_desired_revision(
    node_id: IdType,
    instance_id: XrayInstanceID,
    service: FromDishka[IXrayAssignmentService],
) -> Response:
    await service.clear(node_id, instance_id)
    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
        headers={"Cache-Control": "private, no-store"},
    )


@router.get("/comparison")
async def compare_desired_revision(
    node_id: IdType,
    instance_id: XrayInstanceID,
    response: Response,
    query: FromDishka[IXrayRevisionComparisonQuery],
) -> APIResponse[XrayRevisionComparisonOutput, None]:
    comparison = await query.get(node_id, instance_id)
    response.headers["Cache-Control"] = "private, no-store"
    return APIResponse[XrayRevisionComparisonOutput, None].from_data(
        XrayRevisionComparisonOutput.from_comparison(
            node_id, instance_id, comparison
        )
    )

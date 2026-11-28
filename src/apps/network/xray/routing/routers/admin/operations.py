"""Durably admit Xray routing mutations for authorized Panel operators."""

from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Header, Query, Response, status
from papilio.api.responses.envelope import APIResponse
from papilio.errors.outputs import BaseErrorOut
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.network.xray.instances.domain.dtos.identity import XrayInstanceID

from ...app.interfaces.operations import IXrayRoutingOperations
from ...domain.dtos.identity import RoutingTag
from ...domain.dtos.mutations import (
    AppendRule,
    ClearBalancer,
    RemoveRule,
    ReplaceRules,
    RoutingOverrideInput,
    RoutingReplacementInput,
    RoutingRuleInput,
    SetBalancer,
)
from ...domain.enums.operation import RoutingPayloadFailure
from ...domain.models.operation import XrayRoutingOperationModel
from ..dependencies.cache import no_store
from ..schemas.operations import RoutingOperationOutput

router = APIRouter(
    prefix="/admin/nodes/{node_id:int}/xray/instances/{instance_id}/routing",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network")), Depends(no_store)],
)


@router.post("/rules", status_code=status.HTTP_202_ACCEPTED)
async def append_rule(
    node_id: IdType,
    instance_id: XrayInstanceID,
    data: RoutingRuleInput,
    response: Response,
    key: Annotated[UUID, Header(alias="Idempotency-Key")],
    operations: FromDishka[IXrayRoutingOperations],
) -> APIResponse[RoutingOperationOutput, None]:
    intent = AppendRule(rule=data)
    record = await operations.submit(node_id, instance_id, key, intent)
    return _admission_response(record, response)


@router.post("/replacements", status_code=status.HTTP_202_ACCEPTED)
async def replace_rules(
    node_id: IdType,
    instance_id: XrayInstanceID,
    data: RoutingReplacementInput,
    response: Response,
    key: Annotated[UUID, Header(alias="Idempotency-Key")],
    operations: FromDishka[IXrayRoutingOperations],
) -> APIResponse[RoutingOperationOutput, None]:
    intent = ReplaceRules(rule=data)
    record = await operations.submit(node_id, instance_id, key, intent)
    return _admission_response(record, response)


@router.delete("/rules", status_code=status.HTTP_202_ACCEPTED)
async def remove_rule(
    node_id: IdType,
    instance_id: XrayInstanceID,
    tag: Annotated[RoutingTag, Query()],
    response: Response,
    key: Annotated[UUID, Header(alias="Idempotency-Key")],
    operations: FromDishka[IXrayRoutingOperations],
) -> APIResponse[RoutingOperationOutput, None]:
    intent = RemoveRule(tag=tag)
    record = await operations.submit(node_id, instance_id, key, intent)
    return _admission_response(record, response)


@router.put("/balancer-override", status_code=status.HTTP_202_ACCEPTED)
async def set_balancer_override(
    node_id: IdType,
    instance_id: XrayInstanceID,
    tag: Annotated[RoutingTag, Query()],
    data: RoutingOverrideInput,
    response: Response,
    key: Annotated[UUID, Header(alias="Idempotency-Key")],
    operations: FromDishka[IXrayRoutingOperations],
) -> APIResponse[RoutingOperationOutput, None]:
    intent = SetBalancer(tag=tag, override=data)
    record = await operations.submit(node_id, instance_id, key, intent)
    return _admission_response(record, response)


@router.delete("/balancer-override", status_code=status.HTTP_202_ACCEPTED)
async def clear_balancer_override(
    node_id: IdType,
    instance_id: XrayInstanceID,
    tag: Annotated[RoutingTag, Query()],
    response: Response,
    key: Annotated[UUID, Header(alias="Idempotency-Key")],
    operations: FromDishka[IXrayRoutingOperations],
) -> APIResponse[RoutingOperationOutput, None]:
    intent = ClearBalancer(tag=tag)
    record = await operations.submit(node_id, instance_id, key, intent)
    return _admission_response(record, response)


@router.get("/operations/{id:int}")
async def get_routing_operation(
    node_id: IdType,
    instance_id: XrayInstanceID,
    id: IdType,
    operations: FromDishka[IXrayRoutingOperations],
) -> APIResponse[RoutingOperationOutput, None]:
    record = await operations.get(node_id, instance_id, id)
    return APIResponse[RoutingOperationOutput, None].from_data(
        RoutingOperationOutput.from_obj(record)
    )


def _admission_response(
    record: XrayRoutingOperationModel | RoutingPayloadFailure,
    response: Response,
) -> APIResponse[RoutingOperationOutput, None]:
    if isinstance(record, RoutingPayloadFailure):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        result = APIResponse[RoutingOperationOutput, None](
            success=False,
            error=BaseErrorOut(
                message="Routing request protection is unavailable.",
                message_code="xray_routing_protection_unavailable",
            ),
        )
    else:
        result = APIResponse[RoutingOperationOutput, None].from_data(
            RoutingOperationOutput.from_obj(record)
        )
    return result

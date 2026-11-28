"""Expose bounded live routing reads and simulations to Panel operators."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType

from src.apps.network.xray.instances.domain.dtos.identity import XrayInstanceID

from ...app.interfaces.reads import IXrayRoutingQuery
from ...domain.dtos.identity import RoutingTag
from ...domain.dtos.probe import XrayRouteProbe
from ..dependencies.authorization import require_routing_read
from ..dependencies.cache import no_store
from ..schemas.reads import (
    XrayBalancerInfoOutput,
    XrayBalancerObservationOutput,
    XrayRouteObservationOutput,
    XrayRouteSelectionOutput,
    XrayRoutingRuleOutput,
    XrayRuleListOutput,
)

router = APIRouter(
    prefix="/admin/nodes/{node_id:int}/xray/instances/{instance_id}/routing",
    route_class=DishkaRoute,
    dependencies=[Depends(require_routing_read), Depends(no_store)],
)


@router.get("/rules")
async def list_rules(
    node_id: IdType,
    instance_id: XrayInstanceID,
    query: FromDishka[IXrayRoutingQuery],
) -> APIResponse[XrayRuleListOutput, None]:
    result = await query.list_rules(node_id, instance_id)
    output = XrayRuleListOutput(
        node_id=node_id,
        instance_id=instance_id,
        status=result.status,
        received_at=result.received_at,
        rules=[XrayRoutingRuleOutput.from_obj(row) for row in result.value]
        if result.value is not None
        else None,
    )
    return APIResponse[XrayRuleListOutput, None].from_data(output)


@router.get("/balancer")
async def get_balancer(
    node_id: IdType,
    instance_id: XrayInstanceID,
    tag: Annotated[RoutingTag, Query()],
    query: FromDishka[IXrayRoutingQuery],
) -> APIResponse[XrayBalancerObservationOutput, None]:
    result = await query.get_balancer(node_id, instance_id, tag)
    output = XrayBalancerObservationOutput(
        node_id=node_id,
        instance_id=instance_id,
        tag=tag,
        status=result.status,
        received_at=result.received_at,
        balancer=XrayBalancerInfoOutput.from_obj(result.value)
        if result.value is not None
        else None,
    )
    return APIResponse[XrayBalancerObservationOutput, None].from_data(output)


@router.post("/tests")
async def simulate_route(
    node_id: IdType,
    instance_id: XrayInstanceID,
    data: XrayRouteProbe,
    query: FromDishka[IXrayRoutingQuery],
) -> APIResponse[XrayRouteObservationOutput, None]:
    result = await query.simulate(node_id, instance_id, data)
    output = XrayRouteObservationOutput(
        node_id=node_id,
        instance_id=instance_id,
        status=result.status,
        received_at=result.received_at,
        selection=XrayRouteSelectionOutput.from_obj(result.value)
        if result.value is not None
        else None,
    )
    return APIResponse[XrayRouteObservationOutput, None].from_data(output)

"""Panel views for Xray routing observations."""

from papilio.schemas.outputs import BaseOutput

from src.apps.network.nodes.routers.schemas.observation import (
    NodeObservationOutput,
)


class XrayRoutingRuleOutput(BaseOutput):
    rule_tag: str
    outbound_tag: str


class XrayBalancerInfoOutput(BaseOutput):
    override_target: str | None
    reported_targets: tuple[str, ...] | None


class XrayRouteSelectionOutput(BaseOutput):
    outbound_tag: str
    outbound_group_tags: tuple[str, ...]


class XrayRuleListOutput(NodeObservationOutput):
    instance_id: str
    rules: list[XrayRoutingRuleOutput] | None


class XrayBalancerObservationOutput(NodeObservationOutput):
    instance_id: str
    tag: str
    balancer: XrayBalancerInfoOutput | None


class XrayRouteObservationOutput(NodeObservationOutput):
    instance_id: str
    selection: XrayRouteSelectionOutput | None

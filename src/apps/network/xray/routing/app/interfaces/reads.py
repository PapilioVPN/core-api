"""Typed boundaries for Xray routing reads and simulation."""

from typing import Protocol

from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ...domain.dtos.probe import XrayRouteProbe
from ...domain.results.reads import (
    XrayBalancerInfo,
    XrayRouteSelection,
    XrayRoutingRule,
)


class IXrayRoutingReader(Protocol):
    async def list_rules(
        self, node: NodeModel, instance_id: str
    ) -> NodeObservation[tuple[XrayRoutingRule, ...]]: ...

    async def get_balancer(
        self, node: NodeModel, instance_id: str, tag: str
    ) -> NodeObservation[XrayBalancerInfo]: ...

    async def simulate(
        self, node: NodeModel, instance_id: str, data: XrayRouteProbe
    ) -> NodeObservation[XrayRouteSelection]: ...


class IXrayRoutingQuery(Protocol):
    async def list_rules(
        self, node_id: int, instance_id: str
    ) -> NodeObservation[tuple[XrayRoutingRule, ...]]: ...

    async def get_balancer(
        self, node_id: int, instance_id: str, tag: str
    ) -> NodeObservation[XrayBalancerInfo]: ...

    async def simulate(
        self, node_id: int, instance_id: str, data: XrayRouteProbe
    ) -> NodeObservation[XrayRouteSelection]: ...

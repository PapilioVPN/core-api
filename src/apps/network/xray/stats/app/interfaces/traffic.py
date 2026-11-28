"""Boundary contracts for the native Xray traffic reads."""

from typing import Protocol

from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ...domain.enums.traffic import XrayTrafficScope
from ...domain.results.traffic import XrayTraffic


class IXrayTrafficGateway(Protocol):
    async def get(
        self,
        node: NodeModel,
        instance_id: str,
        scope: XrayTrafficScope,
        name: str,
    ) -> NodeObservation[XrayTraffic]: ...
    async def list(
        self, node: NodeModel, instance_id: str, scope: XrayTrafficScope
    ) -> NodeObservation[tuple[XrayTraffic, ...]]: ...


class IXrayTrafficQuery(Protocol):
    async def get(
        self,
        node_id: int,
        instance_id: str,
        scope: XrayTrafficScope,
        name: str,
    ) -> NodeObservation[XrayTraffic]: ...
    async def list(
        self, node_id: int, instance_id: str, scope: XrayTrafficScope
    ) -> NodeObservation[tuple[XrayTraffic, ...]]: ...

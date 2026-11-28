"""Contracts for live Xray runtime metrics."""

from typing import Protocol

from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ...domain.results.runtime import XrayRuntime


class IXrayRuntimeGateway(Protocol):
    async def read(
        self, node: NodeModel, instance_id: str
    ) -> NodeObservation[XrayRuntime]: ...


class IXrayRuntimeQuery(Protocol):
    async def get(
        self, node_id: int, instance_id: str
    ) -> NodeObservation[XrayRuntime]: ...

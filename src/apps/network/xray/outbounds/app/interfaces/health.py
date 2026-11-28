"""Contracts for live Xray outbound health."""

from typing import Protocol

from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ...domain.results.health import XrayOutboundSample


class IXrayOutboundHealthGateway(Protocol):
    async def read(
        self, node: NodeModel, instance_id: str, tag: str | None
    ) -> NodeObservation[tuple[XrayOutboundSample, ...]]: ...


class IXrayOutboundHealthQuery(Protocol):
    async def get(
        self, node_id: int, instance_id: str, tag: str | None
    ) -> NodeObservation[tuple[XrayOutboundSample, ...]]: ...

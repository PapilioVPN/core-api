"""Contracts for live Xray outbound health."""

from typing import Protocol

from src.apps.network.nodes.domain.models.records import NodeModel
from src.apps.network.nodes.domain.results.observation import NodeObservation

from ...domain.results.health import XrayOutboundSample


class IXrayOutboundHealthGateway(Protocol):
    async def read(
        self, node: NodeModel, instance_id: str, tag: str | None
    ) -> NodeObservation[tuple[XrayOutboundSample, ...]]: ...


class IXrayOutboundHealthQuery(Protocol):
    async def get(
        self, node_id: int, instance_id: str, tag: str | None
    ) -> NodeObservation[tuple[XrayOutboundSample, ...]]: ...

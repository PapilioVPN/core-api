"""Read aggregate VLESS membership from the selected Node execution."""

from typing import Protocol

from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.domain.models.records import NodeModel


class IXrayVlessCountQuery(Protocol):
    async def get(
        self, node_id: int, instance_id: str, inbound_tag: str
    ) -> NodeObservation[int]: ...


class IXrayVlessCountGateway(Protocol):
    async def get(
        self, node: NodeModel, instance_id: str, inbound_tag: str
    ) -> NodeObservation[int]: ...

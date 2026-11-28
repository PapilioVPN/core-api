"""Typed Hysteria status boundary."""

from typing import Protocol

from src.apps.network.nodes.domain.models.records import NodeModel
from src.apps.network.nodes.domain.results.observation import NodeObservation

from ...domain.results.status import HysteriaStatus


class IHysteriaStatusGateway(Protocol):
    async def read(
        self, node: NodeModel, instance_id: str
    ) -> NodeObservation[HysteriaStatus]: ...


class IHysteriaStatusQuery(Protocol):
    async def get(
        self, node_id: int, instance_id: str
    ) -> NodeObservation[HysteriaStatus]: ...

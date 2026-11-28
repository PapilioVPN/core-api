"""Typed contracts for an on-demand Xray instance read."""

from typing import Protocol

from src.apps.network.nodes.domain.results.records import NodeEndpoint

from ...domain.dtos.fleet_status import XrayFleetStatusInput
from ...domain.results.status import XrayFleetStatusItem, XrayStatusResult


class IXrayStatusGateway(Protocol):
    async def read(
        self, node_id: int, address: str, port: int, instance_id: str
    ) -> XrayStatusResult: ...


class IXrayStatusFanout(Protocol):
    async def read(
        self, endpoint: NodeEndpoint, instance_id: str
    ) -> XrayStatusResult: ...


class IXrayStatusQuery(Protocol):
    async def get(
        self, node_id: int, instance_id: str
    ) -> XrayStatusResult: ...

    async def observe_target(
        self, node: NodeEndpoint, instance_id: str
    ) -> XrayStatusResult: ...


class IXrayFleetStatusQuery(Protocol):
    async def get(
        self, data: XrayFleetStatusInput
    ) -> tuple[XrayFleetStatusItem, ...]: ...

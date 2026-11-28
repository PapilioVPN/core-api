"""Typed WireGuard log transport and application contracts."""

from contextlib import AbstractAsyncContextManager
from typing import Protocol

from src.apps.network.nodes.observations.domain.results.logs import LogStream
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ...domain.results.logs import WireGuardLogEvent


class IWireGuardLogsGateway(Protocol):
    def follow(
        self, node: NodeModel, name: str
    ) -> AbstractAsyncContextManager[LogStream[WireGuardLogEvent]]: ...


class IWireGuardLogsQuery(Protocol):
    def follow(
        self, node_id: int, name: str
    ) -> AbstractAsyncContextManager[LogStream[WireGuardLogEvent]]: ...

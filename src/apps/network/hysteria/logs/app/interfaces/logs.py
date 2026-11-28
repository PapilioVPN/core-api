"""Typed Hysteria log transport and application contracts."""

from contextlib import AbstractAsyncContextManager
from typing import Protocol

from src.apps.network.nodes.observations.domain.results.logs import LogStream
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ...domain.results.logs import HysteriaLogEvent


class IHysteriaLogsGateway(Protocol):
    def follow(
        self, node: NodeModel, instance_id: str
    ) -> AbstractAsyncContextManager[LogStream[HysteriaLogEvent]]: ...


class IHysteriaLogsQuery(Protocol):
    def follow(
        self, node_id: int, instance_id: str
    ) -> AbstractAsyncContextManager[LogStream[HysteriaLogEvent]]: ...

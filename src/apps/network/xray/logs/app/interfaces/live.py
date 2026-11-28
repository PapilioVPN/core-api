"""Own one live Xray log subscription within its consumer's scope."""

from contextlib import AbstractAsyncContextManager
from typing import Protocol

from src.apps.network.nodes.observations.domain.results.logs import LogStream
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ...domain.results.live import XrayLogLine


class IXrayLogsQuery(Protocol):
    def follow(
        self, node_id: int, instance_id: str
    ) -> AbstractAsyncContextManager[LogStream[XrayLogLine]]: ...


class IXrayLogsGateway(Protocol):
    def follow(
        self, node: NodeModel, instance_id: str
    ) -> AbstractAsyncContextManager[LogStream[XrayLogLine]]: ...

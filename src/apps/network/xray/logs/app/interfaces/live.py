"""Own one live Xray log subscription within its consumer's scope."""

from contextlib import AbstractAsyncContextManager
from typing import Protocol

from src.apps.network.nodes.domain.models.records import NodeModel

from ...domain.enums.live import XrayLogEnd
from ...domain.results.live import XrayLogFeed


class IXrayLogsQuery(Protocol):
    def follow(
        self, node_id: int, instance_id: str
    ) -> AbstractAsyncContextManager[XrayLogFeed | XrayLogEnd]: ...


class IXrayLogsGateway(Protocol):
    def follow(
        self, node: NodeModel, instance_id: str
    ) -> AbstractAsyncContextManager[XrayLogFeed | XrayLogEnd]: ...

"""Typed OpenVPN log transport and application contracts."""

from contextlib import AbstractAsyncContextManager
from typing import Protocol

from src.apps.network.nodes.observations.domain.results.logs import LogStream
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ...domain.dtos.logs import OpenVPNLogInput
from ...domain.results.logs import OpenVPNLogBatch


class IOpenVPNLogsGateway(Protocol):
    def follow(
        self, node: NodeModel, instance_id: str, selection: OpenVPNLogInput
    ) -> AbstractAsyncContextManager[LogStream[OpenVPNLogBatch]]: ...


class IOpenVPNLogsQuery(Protocol):
    def follow(
        self, node_id: int, instance_id: str, selection: OpenVPNLogInput
    ) -> AbstractAsyncContextManager[LogStream[OpenVPNLogBatch]]: ...

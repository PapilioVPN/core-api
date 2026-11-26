"""Typed contracts for an on-demand Xray instance read."""

from typing import Protocol

from ...domain.results.status import XrayStatusResult


class IXrayStatusGateway(Protocol):
    async def read(
        self, node_id: int, address: str, port: int, instance_id: str
    ) -> XrayStatusResult: ...


class IXrayStatusQuery(Protocol):
    async def get(
        self, node_id: int, instance_id: str
    ) -> XrayStatusResult: ...

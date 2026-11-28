"""Contracts for stored Xray intent and on-demand comparison."""

from typing import Protocol

from src.apps.network.xray.instances.domain.dtos.identity import (
    XrayExecutionKey,
)

from ...domain.models.records import XrayDesiredRevisionModel
from ...domain.results.records import (
    XrayAssignmentSelection,
    XrayDesiredRevision,
    XrayRevisionComparison,
)


class IXrayAssignmentRepository(Protocol):
    async def set_revision(
        self, node_id: int, instance_id: str, revision_id: int
    ) -> XrayDesiredRevisionModel: ...

    async def clear(self, node_id: int, instance_id: str) -> None: ...


class IXrayAssignmentReader(Protocol):
    async def select_one(
        self, node_id: int, instance_id: str
    ) -> XrayDesiredRevision | None: ...

    async def select_desired(
        self, keys: tuple[XrayExecutionKey, ...]
    ) -> dict[XrayExecutionKey, XrayDesiredRevision]: ...


class IXrayAssignmentService(Protocol):
    async def set(
        self, node_id: int, instance_id: str, revision_id: int
    ) -> XrayDesiredRevision: ...

    async def clear(self, node_id: int, instance_id: str) -> None: ...


class IXrayAssignmentQuery(Protocol):
    async def get(
        self, node_id: int, instance_id: str
    ) -> XrayAssignmentSelection: ...


class IXrayRevisionComparisonQuery(Protocol):
    async def get(
        self, node_id: int, instance_id: str
    ) -> XrayRevisionComparison: ...

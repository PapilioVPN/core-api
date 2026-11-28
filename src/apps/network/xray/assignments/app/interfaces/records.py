"""Contracts for stored Xray intent and on-demand comparison."""

from typing import Protocol

from ...domain.models.records import XrayDesiredRevisionModel
from ...domain.results.records import (
    XrayAssignmentSelection,
    XrayDesiredRevision,
    XrayRevisionComparison,
)


class IXrayAssignmentRepository(Protocol):
    async def find(
        self, node_id: int, instance_id: str
    ) -> XrayDesiredRevisionModel | None: ...

    async def set_revision(
        self, node_id: int, instance_id: str, revision_id: int
    ) -> XrayDesiredRevisionModel: ...

    async def clear(self, node_id: int, instance_id: str) -> None: ...


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

"""Separate the joined desired-state read from the live fleet comparison."""

from typing import Protocol

from src.apps.network.xray.instances.domain.dtos.identity import (
    XrayExecutionKey,
)

from ...domain.dtos.fleet_comparison import XrayFleetComparisonInput
from ...domain.results.records import (
    XrayDesiredRevision,
    XrayFleetComparisonItem,
)


class IXrayAssignmentReader(Protocol):
    async def select_desired(
        self, keys: tuple[XrayExecutionKey, ...]
    ) -> dict[XrayExecutionKey, XrayDesiredRevision]: ...


class IXrayFleetComparisonQuery(Protocol):
    async def get(
        self, data: XrayFleetComparisonInput
    ) -> tuple[XrayFleetComparisonItem, ...]: ...

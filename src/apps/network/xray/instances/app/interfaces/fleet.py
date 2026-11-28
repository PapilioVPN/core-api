"""Panel admission and tracking for local Start and Stop selections."""

from typing import Protocol

from ...domain.dtos.fleet import (
    XrayFleetStartInput,
    XrayFleetStopInput,
    XrayFleetTrackingInput,
)
from ...domain.results.fleet import XrayFleetOperationResult


class IXrayFleetStartCommand(Protocol):
    async def start(
        self, data: XrayFleetStartInput
    ) -> tuple[XrayFleetOperationResult, ...]: ...


class IXrayFleetStartQuery(Protocol):
    async def get(
        self, data: XrayFleetTrackingInput
    ) -> tuple[XrayFleetOperationResult, ...]: ...


class IXrayFleetStopCommand(Protocol):
    async def stop(
        self, data: XrayFleetStopInput
    ) -> tuple[XrayFleetOperationResult, ...]: ...


class IXrayFleetStopQuery(Protocol):
    async def get(
        self, data: XrayFleetTrackingInput
    ) -> tuple[XrayFleetOperationResult, ...]: ...

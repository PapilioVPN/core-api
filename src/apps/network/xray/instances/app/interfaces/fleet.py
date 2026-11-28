"""Panel admission and tracking for Xray lifecycle selections."""

from typing import Protocol

from ...domain.dtos.fleet import (
    XrayFleetRestartInput,
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


class IXrayFleetRestartCommand(Protocol):
    async def restart(
        self, revision_id: int, data: XrayFleetRestartInput
    ) -> tuple[XrayFleetOperationResult, ...]: ...


class IXrayFleetRestartQuery(Protocol):
    async def get(
        self, revision_id: int, data: XrayFleetTrackingInput
    ) -> tuple[XrayFleetOperationResult, ...]: ...

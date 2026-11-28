"""Panel fleet admission and outcome tracking for saved revisions."""

from typing import Protocol

from ...domain.dtos.fleet_apply import (
    XrayFleetApplyInput,
    XrayFleetApplyTrackingInput,
)
from ...domain.results.fleet import XrayFleetOperationResult


class IXrayFleetApplyCommand(Protocol):
    async def apply(
        self, revision_id: int, data: XrayFleetApplyInput
    ) -> tuple[XrayFleetOperationResult, ...]: ...


class IXrayFleetApplyQuery(Protocol):
    async def get(
        self, revision_id: int, data: XrayFleetApplyTrackingInput
    ) -> tuple[XrayFleetOperationResult, ...]: ...

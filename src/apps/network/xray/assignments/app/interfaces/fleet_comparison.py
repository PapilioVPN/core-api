"""Contract for live fleet comparison."""

from typing import Protocol

from ...domain.dtos.fleet_comparison import XrayFleetComparisonInput
from ...domain.results.records import XrayFleetComparisonItem


class IXrayFleetComparisonQuery(Protocol):
    async def get(
        self, data: XrayFleetComparisonInput
    ) -> tuple[XrayFleetComparisonItem, ...]: ...

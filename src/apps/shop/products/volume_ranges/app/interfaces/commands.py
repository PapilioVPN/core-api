"""Configure a service's custom volume sales."""

from typing import Protocol

from src.apps.shop.products.volume_ranges.domain.dtos.records import RangeWrite
from src.apps.shop.products.volume_ranges.domain.models.records import (
    VolumeRangeModel,
)


class IRangeCommand(Protocol):
    async def create(
        self, service_id: int, data: RangeWrite
    ) -> VolumeRangeModel: ...

    async def replace(
        self, service_id: int, id: int, data: RangeWrite
    ) -> VolumeRangeModel: ...

"""Configure a service's custom volume sales."""

from typing import Protocol

from src.apps.shop.products.volume_ranges.domain.dtos.records import RangeWrite
from src.apps.shop.products.volume_ranges.domain.models.records import (
    VolumeRangeModel,
)


class IRangeCreateCommand(Protocol):
    async def create(
        self, service_id: int, data: RangeWrite
    ) -> VolumeRangeModel: ...


class IRangeReplaceCommand(Protocol):
    async def replace(
        self, service_id: int, id: int, data: RangeWrite
    ) -> VolumeRangeModel: ...

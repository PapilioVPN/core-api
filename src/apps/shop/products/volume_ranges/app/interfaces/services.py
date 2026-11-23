"""Record operations for service-owned volume ranges."""

from typing import Protocol

from papilio.schemas.results import PagedType

from src.apps.shop.products.volume_ranges.domain.dtos.records import (
    RangeList,
    RangeWrite,
)
from src.apps.shop.products.volume_ranges.domain.models.records import (
    VolumeRangeModel,
)


class IRangeCRUD(Protocol):
    async def create(self, data: VolumeRangeModel) -> VolumeRangeModel: ...

    async def get_by_id(
        self, service_id: int, id: int
    ) -> VolumeRangeModel: ...

    async def list(
        self, service_id: int, data: RangeList
    ) -> PagedType[VolumeRangeModel]: ...

    async def replace(
        self, service_id: int, id: int, data: RangeWrite
    ) -> VolumeRangeModel: ...

    async def remove(self, service_id: int, id: int) -> VolumeRangeModel: ...

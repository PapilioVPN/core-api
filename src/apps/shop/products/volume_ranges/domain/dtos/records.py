"""Validated settings and list inputs for a service's volume ranges."""

from typing import Self

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import PageType, PerPageType
from pydantic import model_validator

from src.apps.shop.products.volume_ranges.domain.dtos.validators.bounds import (
    validate_days,
    validate_volume,
)
from src.apps.shop.products.volume_ranges.domain.types.records import (
    DayType,
    RateType,
    VolumeInput,
    VolumeType,
)


class RangeWrite(BaseDTO):
    min_bytes: VolumeInput
    max_bytes: VolumeInput
    step_bytes: VolumeInput
    price_per_gib: RateType
    min_days: DayType | None = None
    max_days: DayType | None = None
    step_days: DayType | None = None
    is_active: bool = True

    @model_validator(mode="after")
    def check_bounds(self) -> Self:
        """Validate reachable volume and duration bounds."""
        validate_volume(self.min_bytes, self.max_bytes, self.step_bytes)
        validate_days(self.min_days, self.max_days, self.step_days)
        return self


class RangeList(BaseDTO):
    volume_bytes: VolumeType | None = None
    page: PageType = 1
    per_page: PerPageType = 20

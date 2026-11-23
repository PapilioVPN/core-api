"""A customer selection for a custom volume price."""

from papilio.schemas.inputs import BaseDTO

from src.apps.shop.products.volume_ranges.domain.types.records import (
    DayType,
    VolumeType,
)


class QuoteInput(BaseDTO):
    volume_bytes: VolumeType
    days: DayType | None = None

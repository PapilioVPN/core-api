"""HTTP fields for an offered range and its panel record."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput


class RangeOutput(BaseOutput):
    id: int
    service_id: int
    min_bytes: int
    max_bytes: int
    step_bytes: int
    price_per_gib: int
    min_days: int | None
    max_days: int | None
    step_days: int | None


class AdminRangeOutput(RangeOutput):
    is_active: bool
    created_at: datetime
    updated_at: datetime

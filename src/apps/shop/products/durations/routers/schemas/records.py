"""Duration definitions displayed to shop operators."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput

from src.apps.shop.products.durations.domain.enums.start import DurationStart


class DurationOutput(BaseOutput):
    id: int
    days: int
    starts_on: DurationStart
    created_at: datetime

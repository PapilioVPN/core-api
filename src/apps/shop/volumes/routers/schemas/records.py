"""Volume definitions displayed to shop operators."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput

from src.apps.shop.volumes.domain.enums.records import VolumeMode


class VolumeOutput(BaseOutput):
    id: int
    mode: VolumeMode
    size_bytes: int | None
    min_bytes: int | None
    max_bytes: int | None
    step_bytes: int | None
    created_at: datetime

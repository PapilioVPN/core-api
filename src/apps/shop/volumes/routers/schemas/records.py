"""Volume definitions displayed to shop operators."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput


class VolumeOutput(BaseOutput):
    id: int
    size_bytes: int
    created_at: datetime

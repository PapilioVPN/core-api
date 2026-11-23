"""Shop service output for authorized operators."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput


class ServiceOutput(BaseOutput):
    id: int
    title: str
    description: str | None
    is_active: bool
    priority: int
    created_at: datetime
    updated_at: datetime

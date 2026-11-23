"""Customer group definitions returned to the panel."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput


class GroupOutput(BaseOutput):
    id: int
    key: str
    title: str
    min_spend: int
    is_active: bool
    priority: int
    created_at: datetime
    updated_at: datetime

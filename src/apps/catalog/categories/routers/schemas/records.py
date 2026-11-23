"""Category presentation for the administrative API."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput


class CategoryOutput(BaseOutput):
    id: int
    slug: str
    title: str
    description: str | None
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

"""Explicit HTTP output for an access scope."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput


class ScopeOutput(BaseOutput):
    id: int
    key: str
    title: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

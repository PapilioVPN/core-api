"""Customer details visible to authorized panel operators."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput


class ProfileOutput(BaseOutput):
    id: int
    name: str
    mobile: str | None
    note: str | None
    is_blocked: bool
    group_id: int | None
    created_at: datetime
    updated_at: datetime

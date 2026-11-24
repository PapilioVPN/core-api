"""Admin session metadata for the panel."""

from datetime import datetime
from uuid import UUID

from papilio.schemas.outputs import BaseOutput


class SessionOutput(BaseOutput):
    id: UUID
    created_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    user_agent: str | None
    current: bool


class RevokedOutput(BaseOutput):
    count: int

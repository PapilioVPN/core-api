"""Explicit user HTTP output without credentials or persistence inheritance."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput


class UserOutput(BaseOutput):
    id: int
    first_name: str
    last_name: str
    mobile: str
    email: str | None
    role_id: int
    is_active: bool
    is_super_admin: bool
    created_at: datetime
    updated_at: datetime

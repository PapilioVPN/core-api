"""Explicit assignment HTTP output, separate from persistence models."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput


class RoleScopeOutput(BaseOutput):
    id: int
    role_id: int
    scope_id: int
    permissions: int
    created_at: datetime
    updated_at: datetime

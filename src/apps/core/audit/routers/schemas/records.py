"""Audit history returned to operators."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput

from src.apps.core.audit.domain.enums.actions import AuditAction


class AuditOutput(BaseOutput):
    id: int
    actor_id: int
    action: AuditAction
    target_id: str
    created_at: datetime
    role_id: int | None
    scope_id: int | None
    permissions: int | None
    count: int | None

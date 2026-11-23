"""Historical facts supplied by the successful operation's owner."""

from dataclasses import dataclass
from uuid import UUID

from src.apps.core.audit.domain.enums.actions import AuditAction


@dataclass(frozen=True, slots=True)
class AuditEvent:
    action: AuditAction
    target_id: int | UUID
    role_id: int | None = None
    scope_id: int | None = None
    permissions: int | None = None
    count: int | None = None

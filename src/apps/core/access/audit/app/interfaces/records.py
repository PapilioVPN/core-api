"""Audit writes that join the originating administrator operation."""

from collections.abc import Sequence
from typing import Protocol

from src.apps.core.access.audit.domain.dtos.event import AuditEvent
from src.apps.core.access.audit.domain.models.records import AuditModel


class IAuditWriter(Protocol):
    async def record(self, actor_id: int, event: AuditEvent) -> AuditModel: ...
    async def record_many(
        self, actor_id: int, events: Sequence[AuditEvent]
    ) -> Sequence[AuditModel]: ...

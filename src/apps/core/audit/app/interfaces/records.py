"""Audit writes that join the originating administrator operation."""

from collections.abc import Sequence
from typing import Protocol

from src.apps.core.audit.domain.dtos.event import AuditEvent


class IAuditWriter(Protocol):
    async def record(self, actor_id: int, event: AuditEvent) -> None: ...
    async def record_many(
        self, actor_id: int, events: Sequence[AuditEvent]
    ) -> None: ...

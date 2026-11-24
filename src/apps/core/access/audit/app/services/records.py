"""Persist completed operations inside their native transaction."""

from collections.abc import Sequence
from datetime import UTC, datetime

from papilio.infra.db.transaction import current_transaction

from src.apps.core.access.audit.domain.dtos.event import AuditEvent
from src.apps.core.access.audit.domain.models.records import AuditModel
from src.apps.core.access.audit.infra.pg.repositories.records import (
    AuditRepository,
)


def _record(actor_id: int, event: AuditEvent, at: datetime) -> AuditModel:
    """Map trusted operation facts to the stored audit record."""
    return AuditModel(
        actor_id=actor_id,
        action=event.action.value,
        target_id=str(event.target_id),
        created_at=at,
        role_id=event.role_id,
        scope_id=event.scope_id,
        permissions=event.permissions,
        count=event.count,
    )


class AuditService:
    def __init__(self, repo: AuditRepository) -> None:
        """Bind the request's audit repository.

        Args:
            repo: Audit persistence on the same PostgreSQL UoW as commands.

        Returns:
            None.
        """
        self.repo = repo

    async def record(self, actor_id: int, event: AuditEvent) -> None:
        """Append one event in the caller's active transaction.

        Args:
            actor_id: Verified operator account identity.
            event: Facts returned by the successful mutation.

        Returns:
            None after inserting the event.

        Raises:
            RuntimeError: There is no active originating transaction.
        """
        current_transaction()
        await self.repo.create(_record(actor_id, event, datetime.now(UTC)))

    async def record_many(
        self, actor_id: int, events: Sequence[AuditEvent]
    ) -> None:
        """Append the actual results of one bounded batch in one write.

        Args:
            actor_id: Verified operator account identity.
            events: One event per written item. An empty batch skips I/O.

        Returns:
            None after the audit batch is inserted.

        Raises:
            RuntimeError: A nonempty batch has no active transaction.
        """
        if events:
            current_transaction()
            at = datetime.now(UTC)
            await self.repo.bulk_create(
                [_record(actor_id, event, at) for event in events]
            )

"""Persist audit records through the native PostgreSQL repository."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)

from src.apps.core.access.audit.domain.models.records import AuditModel
from src.apps.core.access.audit.infra.pg.tables import AuditTable


class AuditRepository(PGIdentifiedRepository[AuditModel]):
    table = AuditTable

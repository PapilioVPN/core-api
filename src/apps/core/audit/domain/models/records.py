"""Immutable historical facts independent of current resource records."""

from datetime import datetime

from papilio.infra.db.schema.entity import IdentifiedEntity
from papilio.infra.db.schema.fields import (
    BigIntField,
    CharField,
    SmallIntField,
    TimestampField,
)


class AuditModel(IdentifiedEntity):
    actor_id: int = BigIntField()
    action: str = CharField(32)
    target_id: str = CharField(36)
    created_at: datetime = TimestampField()
    role_id: int | None = BigIntField(nullable=True, default=None)
    scope_id: int | None = BigIntField(nullable=True, default=None)
    permissions: int | None = SmallIntField(nullable=True, default=None)
    count: int | None = BigIntField(nullable=True, default=None)

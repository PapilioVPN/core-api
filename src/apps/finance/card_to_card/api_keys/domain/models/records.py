"""Webhook key metadata and its stored digest."""

from datetime import datetime

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import CharField, TimestampField


class APIKeyModel(PersistenceEntity):
    title: str = CharField(55)
    prefix: str = CharField(12)
    digest: str = CharField(64, unique=True)
    expires_at: datetime = TimestampField()
    revoked_at: datetime | None = TimestampField(default=None, nullable=True)

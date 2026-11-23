"""Credential-free evidence that a refresh identity has been consumed."""

from datetime import datetime

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import CharField, TimestampField


class RefreshUseModel(PersistenceEntity):
    audience: str = CharField(255)
    token_id: str = CharField(255)
    expires_at: datetime = TimestampField(index=True)

"""Persisted administrator sessions with UTC-aware lifetime boundaries."""

from datetime import datetime
from uuid import UUID

from papilio.infra.db.schema.entity import BaseEntity
from papilio.infra.db.schema.fields import (
    CharField,
    ForeignKeyField,
    TimestampField,
)
from sqlmodel import Field


class SessionModel(BaseEntity):
    id: UUID = Field(primary_key=True)
    user_id: int = ForeignKeyField("tbl_users.id", ondelete="CASCADE")
    created_at: datetime = TimestampField()
    last_seen_at: datetime = TimestampField()
    expires_at: datetime = TimestampField(index=True)
    user_agent: str | None = CharField(255, nullable=True, default=None)

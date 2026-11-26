"""Stored operator-managed node identity and address."""

from datetime import datetime

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BoolField,
    CharField,
    EnumField,
    IntField,
    TimestampField,
)
from sqlalchemy import text

from ..enums.connection import NodeConnectionStatus


class NodeModel(PersistenceEntity):
    name: str = CharField(55)
    address: str = CharField(253)
    port: int = IntField()
    is_enabled: bool = BoolField(default=True)
    connection_status: NodeConnectionStatus = EnumField(
        NodeConnectionStatus,
        length=12,
        default=NodeConnectionStatus.UNCHECKED,
        server_default=text("'unchecked'"),
    )
    probe_started_at: datetime | None = TimestampField(
        nullable=True, default=None
    )
    last_checked_at: datetime | None = TimestampField(
        nullable=True, default=None
    )
    last_seen_at: datetime | None = TimestampField(nullable=True, default=None)

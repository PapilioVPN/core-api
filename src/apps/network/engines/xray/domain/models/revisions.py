"""Persist exact Xray source bytes only in authenticated encrypted form."""

from datetime import datetime

from papilio.infra.db.schema.entity import IdentifiedEntity
from papilio.infra.db.schema.fields import (
    CharField,
    IntField,
    TextField,
    TimestampField,
)
from sqlalchemy import func


class XrayRevisionModel(IdentifiedEntity):
    config_sha256: str = CharField(64)
    size_bytes: int = IntField()
    ciphertext: str = TextField()
    created_at: datetime = TimestampField(
        server_default=func.current_timestamp()
    )

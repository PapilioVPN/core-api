"""Reusable volume definitions stored in integer bytes."""

from datetime import datetime

from papilio.infra.db.schema.entity import IdentifiedEntity
from papilio.infra.db.schema.fields import (
    BigIntField,
    BoolField,
    TimestampField,
)
from sqlalchemy import func, true


class VolumeModel(IdentifiedEntity):
    size_bytes: int = BigIntField()
    is_canonical: bool = BoolField(default=True, server_default=true())
    created_at: datetime | None = TimestampField(
        default=None,
        server_default=func.current_timestamp(),
    )

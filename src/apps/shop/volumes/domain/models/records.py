"""Reusable volume definitions stored in integer bytes."""

from datetime import datetime

from papilio.infra.db.schema.entity import IdentifiedEntity
from papilio.infra.db.schema.fields import (
    BigIntField,
    EnumField,
    TimestampField,
)
from sqlalchemy import func

from src.apps.shop.volumes.domain.enums.records import VolumeMode


class VolumeModel(IdentifiedEntity):
    mode: VolumeMode = EnumField(VolumeMode, length=8)
    size_bytes: int | None = BigIntField(nullable=True, default=None)
    min_bytes: int | None = BigIntField(nullable=True, default=None)
    max_bytes: int | None = BigIntField(nullable=True, default=None)
    step_bytes: int | None = BigIntField(nullable=True, default=None)
    created_at: datetime | None = TimestampField(
        default=None,
        server_default=func.current_timestamp(),
    )

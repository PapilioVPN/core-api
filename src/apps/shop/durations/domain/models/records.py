"""Reusable definitions of a positive validity period in days."""

from datetime import datetime

from papilio.infra.db.schema.entity import IdentifiedEntity
from papilio.infra.db.schema.fields import EnumField, IntField, TimestampField
from sqlalchemy import func

from src.apps.shop.durations.domain.enums.start import DurationStart


class DurationModel(IdentifiedEntity):
    days: int = IntField()
    starts_on: DurationStart = EnumField(DurationStart, length=16)
    created_at: datetime | None = TimestampField(
        default=None,
        server_default=func.current_timestamp(),
    )

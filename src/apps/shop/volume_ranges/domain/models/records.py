"""Persisted range for custom volume sales under one service."""

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BigIntField,
    BoolField,
    ForeignKeyField,
    IntField,
)


class VolumeRangeModel(PersistenceEntity):
    service_id: int = ForeignKeyField("tbl_services.id", ondelete="RESTRICT")
    min_bytes: int = BigIntField()
    max_bytes: int = BigIntField()
    step_bytes: int = BigIntField()
    price_per_gib: int = BigIntField()
    min_days: int | None = IntField(nullable=True, default=None)
    max_days: int | None = IntField(nullable=True, default=None)
    step_days: int | None = IntField(nullable=True, default=None)
    is_active: bool = BoolField(default=True)

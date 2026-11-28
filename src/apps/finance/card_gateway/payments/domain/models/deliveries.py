"""Durable evidence from authenticated provider deliveries."""

from datetime import datetime

from papilio.infra.db.schema.entity import IdentifiedEntity
from papilio.infra.db.schema.fields import (
    BigIntField,
    CharField,
    ForeignKeyField,
    TextField,
    TimestampField,
)


class DeliveryModel(IdentifiedEntity):
    gateway_id: int = ForeignKeyField(
        "tbl_card_gateways.id", ondelete="RESTRICT"
    )
    delivery_id: str = CharField(255)
    slug: str = TextField()
    attempt_code: str = CharField(255)
    base_amount: int = BigIntField()
    paid_amount: int = BigIntField()
    sent_at: datetime = TimestampField()
    received_at: datetime = TimestampField()

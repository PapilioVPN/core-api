"""Receipt evidence stored independently from payment processing."""

from datetime import datetime

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BigIntField,
    CharField,
    TimestampField,
)


class ReceiptModel(PersistenceEntity):
    image_url: str = CharField(255)
    amount: int | None = BigIntField(nullable=True, default=None)
    paid_at: datetime | None = TimestampField(nullable=True, default=None)

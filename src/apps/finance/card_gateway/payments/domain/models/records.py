"""A hosted card payment and the link issued for it."""

from datetime import datetime

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BigIntField,
    CharField,
    ForeignKeyField,
    TextField,
    TimestampField,
)


class PaymentModel(PersistenceEntity):
    gateway_id: int = ForeignKeyField(
        "tbl_card_gateways.id", ondelete="RESTRICT"
    )
    amount: int = BigIntField()
    link_requested_at: datetime | None = TimestampField(
        nullable=True, default=None
    )
    slug: str | None = TextField(nullable=True, default=None)
    pay_url: str | None = TextField(nullable=True, default=None)
    expires_at: datetime | None = TimestampField(nullable=True, default=None)
    paid_amount: int | None = BigIntField(nullable=True, default=None)
    attempt_code: str | None = CharField(255, nullable=True, default=None)
    confirmed_at: datetime | None = TimestampField(nullable=True, default=None)

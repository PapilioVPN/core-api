"""A bank-reported rial deposit and its optional payment match."""

from datetime import datetime

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BigIntField,
    ForeignKeyField,
    TimestampField,
)


class DepositModel(PersistenceEntity):
    amount: int = BigIntField(index=True)
    paid_at: datetime | None = TimestampField(nullable=True, default=None)
    payment_id: int | None = ForeignKeyField(
        "tbl_payments.id",
        ondelete="RESTRICT",
        nullable=True,
        unique=True,
        default=None,
    )

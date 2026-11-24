"""A payment with its rial amount and bank receipt."""

from datetime import datetime

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BigIntField,
    CharField,
    EnumField,
    ForeignKeyField,
    TimestampField,
)

from ..enums.records import PaymentStatus


class PaymentModel(PersistenceEntity):
    receipt_id: int = ForeignKeyField(
        "tbl_receipts.id", ondelete="RESTRICT", unique=True
    )
    amount: int = BigIntField()
    status: PaymentStatus = EnumField(
        PaymentStatus, length=12, default=PaymentStatus.PENDING
    )
    confirmed_at: datetime | None = TimestampField(nullable=True, default=None)
    rejection_reason: str | None = CharField(500, nullable=True, default=None)

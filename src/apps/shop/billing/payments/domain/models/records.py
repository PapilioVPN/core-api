"""A payment with its original price and optional transfer instructions."""

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
    receipt_id: int | None = ForeignKeyField(
        "tbl_receipts.id",
        ondelete="RESTRICT",
        unique=True,
        nullable=True,
        default=None,
    )
    amount: int = BigIntField()
    transfer_amount: int | None = BigIntField(
        nullable=True, unique=True, default=None
    )
    confirmation_code: str | None = CharField(5, nullable=True, default=None)
    status: PaymentStatus = EnumField(
        PaymentStatus, length=12, default=PaymentStatus.PENDING
    )
    confirmed_at: datetime | None = TimestampField(nullable=True, default=None)
    rejection_reason: str | None = CharField(500, nullable=True, default=None)

    @property
    def auto_confirm(self) -> bool:
        return self.transfer_amount is not None

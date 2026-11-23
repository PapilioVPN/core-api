"""Historical customer transfers with their destination and review facts."""

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
    customer_id: int = ForeignKeyField("tbl_customers.id", ondelete="RESTRICT")
    card_id: int | None = ForeignKeyField(
        "tbl_payment_cards.id", ondelete="SET NULL", nullable=True
    )
    bank_id: int = ForeignKeyField(
        "tbl_banks.id", ondelete="RESTRICT", index=True
    )
    card_last4: str = CharField(4)
    amount: int = BigIntField()
    reference: str = CharField(64)
    paid_at: datetime | None = TimestampField(nullable=True, default=None)
    status: PaymentStatus = EnumField(
        PaymentStatus, length=12, default=PaymentStatus.PENDING
    )
    reviewer_id: int | None = BigIntField(nullable=True, default=None)
    reviewed_at: datetime | None = TimestampField(nullable=True, default=None)

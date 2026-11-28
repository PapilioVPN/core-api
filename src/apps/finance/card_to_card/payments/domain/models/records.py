"""Card payment terms, optional receipt, and review decision."""

from datetime import datetime

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BigIntField,
    CharField,
    EnumField,
    ForeignKeyField,
    TimestampField,
)

from ..enums.records import PaymentMode, PaymentStatus


class CardPaymentModel(PersistenceEntity):
    card_id: int = ForeignKeyField(
        "tbl_payment_cards.id", ondelete="RESTRICT", index=True
    )
    amount: int = BigIntField()
    mode: PaymentMode = EnumField(
        PaymentMode, length=6, default=PaymentMode.MANUAL
    )
    payable_amount: int | None = BigIntField(
        nullable=True, index=True, default=None
    )
    code: str | None = CharField(5, nullable=True, index=True, default=None)
    expires_at: datetime | None = TimestampField(nullable=True, default=None)
    receipt_url: str | None = CharField(255, nullable=True, default=None)
    description: str | None = CharField(500, nullable=True, default=None)
    status: PaymentStatus = EnumField(
        PaymentStatus, length=12, default=PaymentStatus.PENDING
    )
    transfer_id: int | None = ForeignKeyField(
        "tbl_card_transfers.id",
        ondelete="RESTRICT",
        nullable=True,
        unique=True,
        default=None,
    )
    decided_at: datetime | None = TimestampField(nullable=True, default=None)
    rejection_reason: str | None = CharField(500, nullable=True, default=None)

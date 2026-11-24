"""Original bank receipt, observed transfer details and review state."""

from datetime import datetime

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BigIntField,
    CharField,
    EnumField,
    TimestampField,
)

from ..enums.records import ReceiptStatus


class ReceiptModel(PersistenceEntity):
    image_url: str = CharField(255)
    status: ReceiptStatus = EnumField(
        ReceiptStatus, length=12, default=ReceiptStatus.PENDING
    )
    amount: int | None = BigIntField(nullable=True, default=None)
    paid_at: datetime | None = TimestampField(nullable=True, default=None)
    tracking_code: str | None = CharField(55, nullable=True, default=None)
    reference_code: str | None = CharField(55, nullable=True, default=None)
    bank_name: str | None = CharField(100, nullable=True, default=None)
    source_last4: str | None = CharField(4, nullable=True, default=None)
    destination_last4: str | None = CharField(4, nullable=True, default=None)
    rejection_reason: str | None = CharField(500, nullable=True, default=None)

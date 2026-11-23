"""Payment amount in rials, owning resource and submission state."""

from datetime import datetime

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BigIntField,
    EnumField,
    ForeignKeyField,
    TimestampField,
)

from ..enums.records import PaymentSource, PaymentStatus


class PaymentModel(PersistenceEntity):
    customer_id: int = ForeignKeyField("tbl_customers.id", ondelete="RESTRICT")
    source: PaymentSource = EnumField(PaymentSource, length=16)
    source_id: int = BigIntField()
    amount: int = BigIntField()
    status: PaymentStatus = EnumField(
        PaymentStatus, length=12, default=PaymentStatus.PENDING
    )
    submitted_at: datetime | None = TimestampField(nullable=True, default=None)

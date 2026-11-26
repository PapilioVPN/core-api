"""A customer's request to add funds to their wallet."""

from datetime import datetime

from papilio.infra.db.schema.entity import IdentifiedEntity
from papilio.infra.db.schema.fields import (
    BigIntField,
    ForeignKeyField,
    TimestampField,
)
from sqlalchemy import func


class WalletDepositModel(IdentifiedEntity):
    customer_id: int = ForeignKeyField("tbl_customers.id", ondelete="RESTRICT")
    amount: int = BigIntField()
    created_at: datetime | None = TimestampField(
        default=None, server_default=func.current_timestamp()
    )

"""A posted movement against a customer's wallet."""

from datetime import datetime

from papilio.infra.db.schema.entity import IdentifiedEntity
from papilio.infra.db.schema.fields import (
    BigIntField,
    CharField,
    EnumField,
    ForeignKeyField,
    TimestampField,
)
from sqlalchemy import func

from ..enums.records import Direction


class WalletTransactionModel(IdentifiedEntity):
    customer_id: int = ForeignKeyField(
        "tbl_wallet_balances.customer_id", ondelete="RESTRICT"
    )
    direction: Direction = EnumField(Direction, length=6)
    amount: int = BigIntField()
    balance_before: int = BigIntField()
    balance_after: int = BigIntField()
    description: str | None = CharField(500, nullable=True, default=None)
    created_at: datetime | None = TimestampField(
        default=None, server_default=func.current_timestamp()
    )

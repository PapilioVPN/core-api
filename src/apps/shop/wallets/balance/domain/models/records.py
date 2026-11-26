"""One authoritative rial balance per customer."""

from papilio.infra.db.schema.entity import BaseEntity
from papilio.infra.db.schema.fields import BigIntField, ForeignKeyField
from sqlalchemy import text


class WalletBalanceModel(BaseEntity):
    customer_id: int = ForeignKeyField(
        "tbl_customers.id", ondelete="RESTRICT", primary_key=True
    )
    amount: int = BigIntField(default=0, server_default=text("0"))

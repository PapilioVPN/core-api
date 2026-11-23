"""Customer receipts awaiting review."""

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BigIntField,
    CharField,
    ForeignKeyField,
)


class ReceiptModel(PersistenceEntity):
    customer_id: int = ForeignKeyField(
        "tbl_customers.id", ondelete="RESTRICT", index=True
    )
    amount: int = BigIntField()
    image_url: str = CharField(255, index=True)
    status: str = CharField(12, default="pending")

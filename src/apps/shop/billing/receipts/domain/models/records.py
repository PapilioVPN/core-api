"""Raw receipt images submitted as payment evidence."""

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import CharField, ForeignKeyField


class ReceiptModel(PersistenceEntity):
    payment_id: int = ForeignKeyField("tbl_payments.id", ondelete="RESTRICT")
    image_url: str = CharField(255)

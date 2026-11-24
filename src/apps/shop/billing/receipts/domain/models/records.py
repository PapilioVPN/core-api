"""Original uploaded bank receipt and its review state."""

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import CharField, EnumField

from ..enums.records import ReceiptStatus


class ReceiptModel(PersistenceEntity):
    image_url: str = CharField(255)
    status: ReceiptStatus = EnumField(
        ReceiptStatus, length=12, default=ReceiptStatus.PENDING
    )

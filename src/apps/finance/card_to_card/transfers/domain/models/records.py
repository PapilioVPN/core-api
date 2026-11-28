"""An observed bank transfer with its recorded provenance."""

from datetime import datetime

from papilio.infra.db.schema.entity import IdentifiedEntity
from papilio.infra.db.schema.fields import (
    BigIntField,
    EnumField,
    ForeignKeyField,
    TimestampField,
)

from ..enums.records import TransferSource


class TransferModel(IdentifiedEntity):
    amount: int = BigIntField(index=True)
    card_id: int | None = ForeignKeyField(
        "tbl_payment_cards.id",
        ondelete="RESTRICT",
        index=True,
        default=None,
        nullable=True,
    )
    transferred_at: datetime | None = TimestampField(
        default=None, nullable=True
    )
    created_at: datetime = TimestampField()
    source: TransferSource = EnumField(TransferSource, length=8)
    source_id: int = BigIntField()

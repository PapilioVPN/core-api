"""Bank-owned card prefixes stored as text to preserve leading zeros."""

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BoolField,
    CharField,
    ForeignKeyField,
)


class CardPrefixModel(PersistenceEntity):
    bank_id: int = ForeignKeyField(
        "tbl_banks.id", ondelete="CASCADE", index=True
    )
    prefix: str = CharField(8, unique=True)
    is_active: bool = BoolField(default=True)

"""Payment card settings and the issuer resolved when its number was saved."""

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BoolField,
    CharField,
    ForeignKeyField,
)


class PaymentCardModel(PersistenceEntity):
    bank_id: int = ForeignKeyField(
        "tbl_banks.id", ondelete="RESTRICT", index=True
    )
    card_number: str = CharField(16, unique=True)
    holder_name: str = CharField(55)
    is_active: bool = BoolField(default=True)
    allow_manual: bool = BoolField(default=True)
    allow_auto: bool = BoolField(default=False)

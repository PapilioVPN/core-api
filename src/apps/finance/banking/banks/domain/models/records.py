"""Iranian issuer identities and their offline card prefixes."""

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BoolField,
    CharField,
    IntField,
)


class BankModel(PersistenceEntity):
    code: str = CharField(32, unique=True)
    title: str = CharField(55)
    icon_url: str | None = CharField(255, nullable=True, default=None)
    is_active: bool = BoolField(default=True)
    priority: int = IntField(default=0)

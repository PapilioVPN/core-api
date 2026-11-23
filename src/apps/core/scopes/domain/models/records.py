"""Native scope persistence declarations."""

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import BoolField, CharField, TextField


class ScopeModel(PersistenceEntity):
    key: str = CharField(55, unique=True)
    title: str = CharField(55)
    description: str | None = TextField(nullable=True, default=None)
    is_active: bool = BoolField(default=True)

"""Customer groups and their qualifying purchase totals in rials."""

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BigIntField,
    BoolField,
    CharField,
    IntField,
)


class CustomerGroupModel(PersistenceEntity):
    key: str = CharField(55, unique=True)
    title: str = CharField(55)
    min_spend: int = BigIntField(unique=True)
    is_active: bool = BoolField(default=True)
    priority: int = IntField(default=0)

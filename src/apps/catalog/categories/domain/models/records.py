"""Catalog categories available for product navigation."""

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BoolField,
    CharField,
    IntField,
    TextField,
)


class CategoryModel(PersistenceEntity):
    slug: str = CharField(55, unique=True)
    title: str = CharField(55)
    description: str | None = TextField(nullable=True, default=None)
    priority: int = IntField(default=0)
    is_active: bool = BoolField(default=True)

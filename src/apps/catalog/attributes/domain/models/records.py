"""Reusable feature definitions with optional subscription parameter keys."""

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BoolField,
    CharField,
    EnumField,
    TextField,
)

from src.apps.catalog.attributes.domain.enums.records import (
    AttributeType,
    ParamKey,
)


class AttributeModel(PersistenceEntity):
    key: str = CharField(35, unique=True)
    label: str = CharField(55)
    type: AttributeType = EnumField(AttributeType, length=10)
    description: str | None = TextField(nullable=True, default=None)
    param_key: ParamKey | None = EnumField(
        ParamKey, length=24, unique=True, nullable=True, default=None
    )
    is_active: bool = BoolField(default=True)

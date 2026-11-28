"""The stored global policy for automatic card transfers."""

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BoolField,
    EnumField,
    IntField,
    SmallIntField,
)

from ..enums.records import SettingsKey


class TransferSettingsModel(PersistenceEntity):
    key: SettingsKey = EnumField(SettingsKey, length=55, unique=True)
    auto_confirm: bool = BoolField(default=False)
    digits: int = SmallIntField(default=4)
    window_minutes: int | None = IntField(default=None, nullable=True)

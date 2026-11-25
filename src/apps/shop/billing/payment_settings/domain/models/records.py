"""Global automatic payment policy and the current hook key digest."""

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import BoolField, CharField, SmallIntField


class PaymentSettingsModel(PersistenceEntity):
    auto_confirm: bool = BoolField(default=False)
    digits: int = SmallIntField(default=5)
    window_hours: int = SmallIntField(default=24)
    key_hash: str | None = CharField(64, nullable=True, default=None)

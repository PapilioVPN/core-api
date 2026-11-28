"""Store card gateway metadata and its protected provider configuration."""

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BoolField,
    CharField,
    EnumField,
    TextField,
)

from ..enums.records import GatewayKind


class GatewayModel(PersistenceEntity):
    kind: GatewayKind = EnumField(GatewayKind, length=32, unique=True)
    title: str = CharField(55)
    icon_url: str | None = TextField(default=None, nullable=True)
    is_active: bool = BoolField(default=False)

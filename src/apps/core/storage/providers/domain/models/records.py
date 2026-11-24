"""S3-compatible connection metadata and separately stored configuration."""

from papilio.infra.db.dialects.postgresql import JSONBField
from papilio.infra.db.schema.entity import PersistenceEntity, TimestampEntity
from papilio.infra.db.schema.fields import (
    BoolField,
    CharField,
    ForeignKeyField,
    TextField,
)
from pydantic import JsonValue


class StorageProviderModel(PersistenceEntity):
    key: str = CharField(55, unique=True)
    title: str = CharField(55)
    description: str | None = TextField(nullable=True, default=None)
    is_active: bool = BoolField(default=False)


class StorageProviderConfigModel(TimestampEntity):
    provider_id: int = ForeignKeyField(
        "tbl_storage_providers.id", primary_key=True, ondelete="CASCADE"
    )
    config: dict[str, JsonValue] = JSONBField(default_factory=dict)

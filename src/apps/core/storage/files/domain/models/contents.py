"""Physical content identity and its recorded storage location."""

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BigIntField,
    CharField,
    EnumField,
    ForeignKeyField,
    TextField,
)

from src.apps.core.storage.configs.domain.enums.backends import StorageBackend


class FileContentModel(PersistenceEntity):
    """One stored content per SHA-256, shared across logical files.

    storage_key is the absolute local filename or the exact S3 object key.
    The S3 bucket, endpoint and region record the original destination without
    credentials; provider_id identifies the connection used for access.
    """

    sha256: str = CharField(64, unique=True)
    size_bytes: int = BigIntField()
    backend: StorageBackend = EnumField(StorageBackend, length=5)
    storage_key: str = TextField()
    url: str | None = TextField(nullable=True, default=None)
    provider_id: int | None = ForeignKeyField(
        "tbl_storage_providers.id",
        ondelete="RESTRICT",
        nullable=True,
        default=None,
        index=True,
    )
    bucket: str | None = TextField(nullable=True, default=None)
    endpoint_url: str | None = TextField(nullable=True, default=None)
    region_name: str | None = TextField(nullable=True, default=None)

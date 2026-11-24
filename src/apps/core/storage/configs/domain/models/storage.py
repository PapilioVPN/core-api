"""The global backend selection, separate from connection credentials."""

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import EnumField

from src.apps.core.storage.configs.domain.enums.backends import StorageBackend


class StorageConfigModel(PersistenceEntity):
    backend: StorageBackend = EnumField(StorageBackend, length=5)

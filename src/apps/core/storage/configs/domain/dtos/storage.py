"""Complete input for the single shared destination selection."""

from papilio.schemas.inputs import BaseDTO

from src.apps.core.storage.configs.domain.enums.backends import StorageBackend


class StorageConfigWrite(BaseDTO):
    backend: StorageBackend

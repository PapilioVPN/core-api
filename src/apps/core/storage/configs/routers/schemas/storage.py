"""Explicit output for the global storage destination setting."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput

from src.apps.core.storage.configs.domain.enums.backends import StorageBackend


class StorageConfigOutput(BaseOutput):
    id: int
    backend: StorageBackend
    created_at: datetime
    updated_at: datetime

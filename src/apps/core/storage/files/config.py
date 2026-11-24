"""Local file storage settings, extending the native filesystem contract."""

from papilio.core.config import StorageConfig
from pydantic import HttpUrl


class FileStorageConfig(StorageConfig):
    public_base_url: HttpUrl | None = None

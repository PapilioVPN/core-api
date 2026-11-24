"""Storage mechanisms supported by the application."""

from enum import StrEnum


class StorageBackend(StrEnum):
    LOCAL = "local"
    S3 = "s3"

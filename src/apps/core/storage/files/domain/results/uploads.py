"""Materialized upload results and destinations without live resources."""

from dataclasses import dataclass, field

from src.apps.core.storage.files.domain.models.records import FileModel
from src.apps.core.storage.providers.domain.results.records import (
    StorageProviderConnection,
)


@dataclass(frozen=True, slots=True)
class FileUploadResult:
    """Committed logical file and its stable access URL."""

    file: FileModel
    url: str


@dataclass(frozen=True, slots=True)
class FileUploadDestination:
    """A new write: local when s3_connection is absent, otherwise that S3.

    Preparation returns None instead of this record for already stored content.
    """

    s3_connection: StorageProviderConnection | None = field(
        default=None, repr=False
    )

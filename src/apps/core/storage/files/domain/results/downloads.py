"""Materialized download preparation and an operation-owned byte stream."""

from dataclasses import dataclass, field

from anyio.abc import ByteReceiveStream

from src.apps.core.storage.providers.domain.dtos.configs import S3Config


@dataclass(frozen=True, slots=True)
class FileDownloadMetadata:
    file_id: int
    original_name: str
    mime_type: str
    size_bytes: int
    sha256: str
    storage_key: str


@dataclass(frozen=True, slots=True)
class PreparedFileDownload:
    """No live SQL resources; absent S3 configuration means local storage."""

    metadata: FileDownloadMetadata
    s3_config: S3Config | None = field(default=None, repr=False)


@dataclass(frozen=True, slots=True)
class FileDownload:
    metadata: FileDownloadMetadata
    source: ByteReceiveStream

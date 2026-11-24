"""Metadata preparation and context-owned local/S3 download contracts."""

from contextlib import AbstractAsyncContextManager
from typing import Protocol

from src.apps.core.storage.files.domain.results.downloads import (
    FileDownload,
    PreparedFileDownload,
)


class IFileDownloadExecution(Protocol):
    async def prepare(self, id: int) -> PreparedFileDownload:
        """Resolve trusted logical/content records in a short SQL request.

        Args:
            id: Internal logical file identity, authorized by the consumer.
        Returns:
            Materialized metadata plus S3 access configuration when required;
            no live database resources leave preparation.
        Raises:
            NotFoundException: A file/content record or original provider
                configuration is absent.
            ValidationException: Recorded S3 location/configuration is invalid.
        """
        ...


class IFileDownload(Protocol):
    def open(self, id: int) -> AbstractAsyncContextManager[FileDownload]:
        """Open a bounded native byte stream after resolving metadata.

        Args:
            id: Internal logical file identity; consumer owns authorization.
        Returns:
            An async context yielding metadata and a stream from byte zero.
            Keep it open while consuming bounded receive() calls. Its stream
            is closed on completion, consumer failure or cancellation.
        Raises:
            NotFoundException: A file/content record or original provider
                configuration is absent.
            ValidationException: Recorded S3 location/configuration is invalid.
            RuntimeError: An ambient SQL transaction would cross streaming.
            Exception: File/SDK access fails; stored metadata is preserved.
        """
        ...

"""Resolve file metadata, then stream outside its SQL request."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from src.apps.core.storage.files.app.interfaces.downloads import (
    IFileDownloadExecution,
)
from src.apps.core.storage.files.app.interfaces.local import ILocalFileStorage
from src.apps.core.storage.files.app.interfaces.s3 import IS3FileStorage
from src.apps.core.storage.files.domain.results.downloads import (
    FileDownload,
)


class FileDownloadPipeline:
    def __init__(
        self,
        execution: IFileDownloadExecution,
        local: ILocalFileStorage,
        s3: IS3FileStorage,
    ) -> None:
        """Bind preparation and the database-independent local/S3 adapters.

        Args:
            execution: Short native request returning materialized metadata.
            local: Existing APP adapter for recorded-path byte streams.
            s3: Existing APP adapter for scoped native S3 byte streams.
        Returns:
            None. No request/session/stream is retained between calls.
        """
        self.execution = execution
        self.local = local
        self.s3 = s3

    @asynccontextmanager
    async def open(self, id: int) -> AsyncGenerator[FileDownload]:
        """Resolve the recorded location before opening its scoped byte stream.

        Args:
            id: Authorized internal logical file identity, not a public path.
        Returns:
            Async context yielding recorded metadata and a native byte stream.
            Original names/MIME/size/hash come from records; bytes are not
            buffered, rehashed or rewritten. Native context exit closes the
            stream on normal completion, consumer failure and cancellation.
        Raises:
            Exception: Metadata/configuration and local/S3 errors propagate;
                no records, current settings or physical bytes are modified.
        """
        prepared = await self.execution.prepare(id)
        metadata = prepared.metadata
        if prepared.s3_config is None:
            stream = self.local.open(Path(metadata.storage_key))
        else:
            stream = self.s3.open(
                prepared.s3_config, storage_key=metadata.storage_key
            )
        async with stream as source:
            yield FileDownload(metadata, source)

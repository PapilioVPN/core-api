"""Coordinate streaming, scoped SQL phases and the configured file adapter."""

from collections.abc import Awaitable, Callable

from anyio.abc import ByteReceiveStream

from src.apps.core.storage.configs.domain.enums.backends import StorageBackend
from src.apps.core.storage.files.app.helpers.urls import build_file_url
from src.apps.core.storage.files.app.interfaces.local import ILocalFileStorage
from src.apps.core.storage.files.app.interfaces.s3 import IS3FileStorage
from src.apps.core.storage.files.app.interfaces.uploads import (
    IFileUploadExecution,
)
from src.apps.core.storage.files.config import FileStorageConfig
from src.apps.core.storage.files.domain.dtos.uploads import FileUpload
from src.apps.core.storage.files.domain.models.contents import FileContentModel
from src.apps.core.storage.files.domain.results.staging import StagedFile
from src.apps.core.storage.files.domain.results.uploads import (
    FileUploadDestination,
    FileUploadResult,
)
from src.apps.core.storage.files.infra.content.staging import FileStager


class FileUploadPipeline:
    def __init__(
        self,
        stager: FileStager,
        local: ILocalFileStorage,
        s3: IS3FileStorage,
        execution: IFileUploadExecution,
        config: FileStorageConfig,
    ) -> None:
        """Bind APP tools and scoped SQL operations without an open request.

        Args:
            stager: Stream hashing and operation-owned temporary files.
            local: Database-independent atomic local publication adapter.
            s3: Database-independent conditional S3 transfer adapter.
            execution: Native SQL read and coordinated-write boundaries.
            config: Native local settings with the explicit public file root.
        Returns:
            None. No request/session/stream is retained between operations.
        """
        self.stager = stager
        self.local = local
        self.s3 = s3
        self.execution = execution
        self.config = config

    async def upload(
        self,
        source: ByteReceiveStream,
        data: FileUpload,
        *,
        max_bytes: int,
        validator: Callable[[StagedFile], Awaitable[None]] | None = None,
    ) -> FileUploadResult:
        """Stage, resolve deduplication, publish if needed and commit metadata.

        Args:
            source: Caller-owned stream, consumed from its current position.
            data: Validated original name and declared MIME; no MIME inference.
            max_bytes: Owner-selected maximum bytes, including zero for EOF.
            validator: Read-only check of the existing staged file, before any
                SQL work or physical publication. Omission preserves behavior.
        Returns:
            Committed logical file and stable URL. Matching content is
            reused across destinations without another copy or configuration.
        Raises:
            Exception: Stream, limit, storage, configuration, collision and SQL
                failures propagate. Staging is cleaned; published bytes survive
                later SQL failure. The borrowed source is never closed here.
        """
        async with self.stager.stage(source, max_bytes=max_bytes) as staged:
            if validator is not None:
                await validator(staged)
            published = None
            destination = await self.execution.prepare(staged.sha256)
            if destination is not None:
                published = await self._publish(
                    staged, destination, mime_type=data.mime_type
                )
            result = await self.execution.complete(
                data, sha256=staged.sha256, published=published
            )
        return result

    async def _publish(
        self,
        staged: StagedFile,
        destination: FileUploadDestination,
        *,
        mime_type: str,
    ) -> FileContentModel | None:
        """Publish once and describe only the location actually used.

        Args:
            staged: Complete hashed source kept alive by the upload context.
            destination: Materialized selection; absent S3 means local storage.
            mime_type: Caller-declared MIME for the remote object.
        Returns:
            Trusted new metadata without credentials; None on an existing key.
            Completion separately checks for a committed matching content row.
        Raises:
            Exception: Physical adapter failures propagate without DB writes
                or a fallback destination. Accepted bytes are never deleted.
        """
        published = None
        connection = destination.s3_connection
        key = f"{staged.sha256[:2]}/{staged.sha256}"
        if connection is None:
            url = build_file_url(self.config.public_base_url, key)
            path = await self.local.save_if_absent(staged)
            if path is not None:
                published = FileContentModel(
                    sha256=staged.sha256,
                    size_bytes=staged.size_bytes,
                    backend=StorageBackend.LOCAL,
                    storage_key=str(path),
                    url=url,
                )
        else:
            config = connection.config
            url = build_file_url(config.public_base_url, key)
            key = await self.s3.save_if_absent(
                staged,
                config,
                storage_key=key,
                mime_type=mime_type,
            )
            if key is not None:
                published = FileContentModel(
                    sha256=staged.sha256,
                    size_bytes=staged.size_bytes,
                    backend=StorageBackend.S3,
                    storage_key=key,
                    url=url,
                    provider_id=connection.provider_id,
                    bucket=config.bucket,
                    endpoint_url=(
                        str(config.endpoint_url)
                        if config.endpoint_url
                        else None
                    ),
                    region_name=config.region_name,
                )
        return published

"""Stream upload and its short native SQL execution phases."""

from collections.abc import Awaitable, Callable
from typing import Protocol

from anyio.abc import ByteReceiveStream

from src.apps.core.storage.files.domain.dtos.uploads import FileUpload
from src.apps.core.storage.files.domain.models.contents import FileContentModel
from src.apps.core.storage.files.domain.results.staging import StagedFile
from src.apps.core.storage.files.domain.results.uploads import (
    FileUploadDestination,
    FileUploadResult,
)


class IFileUploadExecution(Protocol):
    async def prepare(self, sha256: str) -> FileUploadDestination | None:
        """Resolve global deduplication and a new write's destination.

        Args:
            sha256: Trusted digest from the staging operation.
        Returns:
            None for registered content anywhere; otherwise a materialized
            local destination or active S3 connection, without an open request.
        Raises:
            NotFoundException: New content has no selection or active provider.
            ValidationException: The selected S3 configuration is unusable.
        """
        ...

    async def complete(
        self,
        data: FileUpload,
        *,
        sha256: str,
        published: FileContentModel | None,
    ) -> FileUploadResult:
        """Commit a reference, registering new content only when published.

        Args:
            data: Validated original name and declared MIME.
            sha256: Trusted content digest.
            published: New physical metadata, or None without publication.
        Returns:
            Committed logical file and the original shared content's URL.
        Raises:
            ConflictException: No content or new publication exists, or a
                competing registration wins the unique digest constraint.
            ValidationException: Existing content has no recorded access URL.
        """
        ...


class IFileUpload(Protocol):
    async def upload(
        self,
        source: ByteReceiveStream,
        data: FileUpload,
        *,
        max_bytes: int,
        validator: Callable[[StagedFile], Awaitable[None]] | None = None,
    ) -> FileUploadResult:
        """Stage/hash a stream and commit an independent logical reference.

        Args:
            source: Borrowed stream; the caller owns closure and access policy.
            data: Original name and declared MIME. Consumer owns MIME policy.
            max_bytes: Explicit byte limit; zero permits only empty content.
            validator: Optional owner-specific read-only content check, called
                once after staging and before deduplication/publication.
        Returns:
            Committed logical file and stable URL. Equal content reuses its
            original location and URL without an additional query.
        Raises:
            ConflictException: Existing storage key has no content record,
                or concurrent content registration wins the unique constraint.
            RuntimeError: An ambient SQL transaction would cross file I/O.
            ValidationException: A public root is missing/invalid for a new
                upload, or existing content has no recorded URL.
            Exception: Stream, staging, storage and SQL failures propagate.
                Published files survive later SQL failure; no deletion/adoption
                or distributed transaction is implied.
        """
        ...

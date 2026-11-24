"""Local content publication and scoped download contracts."""

from contextlib import AbstractAsyncContextManager
from pathlib import Path
from typing import Protocol

from anyio.abc import ByteReceiveStream

from src.apps.core.storage.files.domain.results.staging import StagedFile


class ILocalFileStorage(Protocol):
    async def save_if_absent(self, data: StagedFile) -> Path | None:
        """Publish bytes or report an existing destination without adoption.

        Args:
            data: Trusted staged bytes kept inside their owning context.
        Returns:
            Newly published absolute path, or None on a destination collision.
            None establishes neither file validity nor registration.
        Raises:
            OSError: A failure other than the final destination collision.
        """
        ...

    async def save(self, data: StagedFile) -> Path:
        """Copy prepared bytes and atomically publish without replacing a file.

        Args:
            data: Trusted FileStager output, used inside its owning context.
                The caller keeps the source unchanged during this operation.
        Returns:
            Absolute original storage path under the configured local root.
            The source remains caller-owned; no database record is written.
        Raises:
            FileExistsError: The hash path exists; app owns deduplication.
            OSError: Copy, size verification or atomic publication fails.
        """
        ...

    def open(
        self, storage_key: Path
    ) -> AbstractAsyncContextManager[ByteReceiveStream]:
        """Open a native download stream with a scoped file lifetime.

        Args:
            storage_key: Trusted original absolute path read from metadata,
                never an unchecked HTTP path. It can belong to an older root.
        Returns:
            A context yielding a stream from byte zero, closed on exit.
        Raises:
            OSError: The recorded file cannot be opened.
            BrokenResourceError: A native stream read fails.
        """
        ...

"""Bounded stream hashing and context-owned temporary file preparation."""

import hashlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from anyio import EndOfStream, TemporaryDirectory, open_file
from anyio.abc import ByteReceiveStream

from src.apps.core.storage.files.domain.results.staging import StagedFile
from src.shared.utils.asyncio.threads import ThreadRunner

CHUNK_SIZE = 1024 * 1024


class FileStager:
    def __init__(
        self, threads: ThreadRunner, *, directory: Path | None = None
    ) -> None:
        """Bind blocking-I/O execution and an optional temporary-file parent.

        Args:
            threads: Worker-thread runner for chunk writes and hashing.
            directory: Existing temporary parent, or the system location.

        Returns:
            None. No file or directory is opened during construction.
        """
        self.threads = threads
        self.directory = directory

    @asynccontextmanager
    async def stage(
        self, source: ByteReceiveStream, *, max_bytes: int
    ) -> AsyncIterator[StagedFile]:
        """Hash and stage a stream using receive blocks of at most one MiB.

        Args:
            source: Borrowed native stream, read from its current position.
                The caller closes it; receive honors the requested bound.
            max_bytes: Caller-selected byte limit; zero allows only EOF.

        Returns:
            An async context yielding path, SHA-256 and actual byte count after
            the file is closed/flushed. The path exists inside that context;
            native cleanup removes it on success, failure and cancellation.

        Raises:
            ValueError: max_bytes is negative or the input exceeds it.
            OSError: File I/O fails or a write is incomplete.
            Exception: Source errors propagate unchanged.
        """
        if max_bytes < 0:
            raise ValueError("max_bytes must be nonnegative")
        parent = str(self.directory) if self.directory is not None else None
        async with TemporaryDirectory(
            prefix="core-api-upload-", dir=parent
        ) as directory:
            path = Path(directory) / "content"
            digest = hashlib.sha256()
            size_bytes = 0
            async with await open_file(path, "xb") as target:

                def write_chunk(chunk: bytes) -> None:
                    """Write and hash one bounded chunk outside the event loop.

                    Args:
                        chunk: One already size-checked received block.

                    Returns:
                        None. The digest advances only after a full write.

                    Raises:
                        OSError: The target cannot accept the complete block.
                    """
                    written = target.wrapped.write(chunk)
                    if written != len(chunk):
                        raise OSError("Incomplete temporary-file write")
                    digest.update(chunk)

                while True:
                    try:
                        chunk = await source.receive(
                            min(CHUNK_SIZE, max_bytes - size_bytes + 1)
                        )
                    except EndOfStream:
                        break
                    if size_bytes + len(chunk) > max_bytes:
                        raise ValueError("File exceeds max_bytes")
                    await self.threads.run(write_chunk, chunk)
                    size_bytes += len(chunk)
            yield StagedFile(path, digest.hexdigest(), size_bytes)

"""Local content publication using native bounded file I/O."""

import errno
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from anyio import Path as AsyncPath
from anyio import TemporaryDirectory
from anyio.abc import ByteReceiveStream
from anyio.streams.file import FileReadStream
from papilio.infra.files.reader import FileReader
from papilio.infra.files.writer import FileWriter

from src.apps.core.storage.files.domain.results.staging import StagedFile

CHUNK_SIZE = 1024 * 1024


class LocalFileStorage:
    def __init__(self, *, root: Path) -> None:
        """Bind the local destination without opening filesystem resources.

        Args:
            root: Configured local storage directory; save resolves it to an
                absolute path. Existing downloads retain their recorded path.
        Returns:
            None.
        """
        self.root = root
        self.reader = FileReader()
        self.writer = FileWriter()

    async def save(self, data: StagedFile) -> Path:
        """Copy bounded chunks, then publish the complete file atomically.

        Args:
            data: Trusted FileStager output with a lowercase SHA-256 digest.
                The caller retains its context and keeps its bytes unchanged.
        Returns:
            Absolute path root/digest-prefix/digest. The source is preserved.
            Only the owned temporary copy is cleaned on failure/cancellation.
            Publication is separate from any subsequent database transaction.
        Raises:
            FileExistsError: The final path exists and is never overwritten.
            OSError: Copy/size verification/publication fails. The filesystem
                must support hard links for atomic no-replace publication.
        """
        destination = await self.save_if_absent(data)
        if destination is None:
            root = Path(await AsyncPath(self.root).resolve())
            path = root / data.sha256[:2] / data.sha256
            raise FileExistsError(errno.EEXIST, "File exists", str(path))
        return destination

    async def save_if_absent(self, data: StagedFile) -> Path | None:
        """Copy prepared bytes and report only a final-path collision as None.

        Args:
            data: Trusted staged output; caller owns its unchanged source.
        Returns:
            Absolute newly published path, or None if the destination exists.
            Existing bytes are never adopted, replaced or deleted.
        Raises:
            OSError: Source, copy, size and directory errors propagate.
        """
        root = Path(await AsyncPath(self.root).resolve())
        directory = root / data.sha256[:2]
        destination = directory / data.sha256
        await AsyncPath(directory).mkdir(parents=True, exist_ok=True)
        async with TemporaryDirectory(
            prefix=".upload-", dir=str(directory)
        ) as temp:
            temporary = Path(temp) / "content"
            async with self.reader.open_bytes(data.path) as source:
                copied = await self.writer.write_stream(
                    temporary,
                    self.reader.chunks(source, CHUNK_SIZE),
                    mode="xb",
                )
            if copied != data.size_bytes:
                raise OSError("Prepared file size changed during local copy")
            try:
                await AsyncPath(destination).hardlink_to(temporary)
            except FileExistsError:
                destination = None
        return destination

    @asynccontextmanager
    async def open(
        self, storage_key: Path
    ) -> AsyncIterator[ByteReceiveStream]:
        """Read the original stored path without loading the whole file.

        Args:
            storage_key: Trusted original metadata path, including an old
                destination after a root/backend change; not external input.
        Returns:
            A scoped native stream from byte zero. Its caller requests bounded
            receive sizes; native cleanup closes the file on context exit.
        Raises:
            OSError: The stored path cannot be opened.
            BrokenResourceError: A native stream read fails.
        """
        async with await FileReadStream.from_path(storage_key) as source:
            yield source

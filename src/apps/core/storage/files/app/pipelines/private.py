"""Stage and read private content with the existing local Storage adapter."""

from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager
from pathlib import Path

from anyio.abc import ByteReceiveStream

from src.apps.core.storage.files.domain.results.staging import StagedFile
from src.apps.core.storage.files.infra.local import LocalFileStorage
from src.apps.core.storage.files.infra.staging import FileStager


class PrivateFiles:
    def __init__(self, root: Path, stager: FileStager) -> None:
        self.root = root
        self.stager = stager

    async def upload(
        self,
        source: ByteReceiveStream,
        directory: str,
        *,
        max_bytes: int,
        validator: Callable[[StagedFile], Awaitable[None]],
    ) -> str:
        """Stage, validate and atomically store private bytes.

        Args:
            source: Borrowed stream, closed by its caller.
            directory: Trusted single path segment under private storage.
            max_bytes: Maximum accepted bytes.
            validator: Consumer's validation of the staged content.

        Returns:
            The content digest, reused for repeated uploads in the directory.
        """
        storage = LocalFileStorage(root=self.root / directory)
        async with self.stager.stage(source, max_bytes=max_bytes) as staged:
            await validator(staged)
            await storage.save_if_absent(staged)
        return staged.sha256

    def open(
        self, directory: str, digest: str
    ) -> AbstractAsyncContextManager[ByteReceiveStream]:
        """Open the stored bytes without exposing their filesystem path.

        Args:
            directory: Trusted single path segment used for the upload.
            digest: Validated lowercase SHA-256 digest.

        Returns:
            The stream context, which raises FileNotFoundError on absence.
        """
        storage = LocalFileStorage(root=self.root / directory)
        return storage.open(storage.root / digest[:2] / digest)

"""Stage bounded uploads and atomically publish local content."""

from collections.abc import Awaitable, Callable
from hashlib import sha256
from pathlib import Path
from re import fullmatch

from anyio import Path as AsyncPath
from anyio import TemporaryDirectory
from anyio.abc import ByteReceiveStream
from papilio.core.config import Settings
from papilio.errors.exceptions import NotFoundException
from papilio.infra.db.transaction import active_transaction
from papilio.infra.files.reader import FileReader
from papilio.infra.files.writer import FileWriter

from ..app.errors import FileTooLarge


class LocalStorage:
    def __init__(self, settings: Settings) -> None:
        """Bind the native storage configuration and file operations.

        Args:
            settings: Native content, staging and byte-limit settings.

        Returns:
            None.
        """
        config = settings.storage
        self.root = Path(config.path)
        self.temp = Path(config.temp_dir)
        self.max_bytes = config.max_file_size
        self.reader = FileReader()
        self.writer = FileWriter()

    async def upload(
        self,
        source: ByteReceiveStream,
        *,
        base_url: str,
        suffix: str,
        validate: Callable[[Path], Awaitable[None]],
    ) -> str:
        """Validate staged bytes before publishing the complete file.

        Args:
            source: Borrowed upload stream, closed by its caller.
            base_url: Consumer-owned download URL prefix.
            suffix: Trusted lowercase extension without a dot.
            validate: Read-only inspection of the complete staged file.

        Returns:
            Stable address of the stored bytes, reused for identical content.

        Raises:
            FileTooLarge: The received body exceeded the configured ceiling.
            RuntimeError: The caller has an active transaction.
            OSError: Staging or publication failed.
        """
        if active_transaction() is not None:
            raise RuntimeError("Upload requires a separate SQL scope")
        if not fullmatch(r"[a-z0-9]{1,8}", suffix):
            raise ValueError("Invalid storage suffix")

        await AsyncPath(self.temp).mkdir(
            mode=0o700, parents=True, exist_ok=True
        )
        digest = sha256()
        size = 0
        async with TemporaryDirectory(dir=str(self.temp)) as directory:
            staged = Path(directory) / "content"
            async with self.writer.open_bytes(staged, mode="xb") as stream:
                async for chunk in source:
                    size += len(chunk)
                    if size > self.max_bytes:
                        raise FileTooLarge(
                            "File exceeds the upload byte limit"
                        )
                    digest.update(chunk)
                    await stream.write(chunk)
            await validate(staged)
            name = f"{digest.hexdigest()}.{suffix}"
            await self._publish(staged, name, size)
        return f"{base_url.rstrip('/')}/{name}"

    async def get_path(self, name: str) -> Path:
        """Resolve a stored filename to its internal path.

        Args:
            name: Content digest and extension from the download address.

        Returns:
            The existing file path under the configured storage root.

        Raises:
            NotFoundException: The name is invalid or the file is missing.
        """
        path = self.root / name[:2] / name
        if not fullmatch(r"[0-9a-f]{64}\.[a-z0-9]{1,8}", name) or not (
            await AsyncPath(path).is_file()
        ):
            raise NotFoundException(
                message="File not found.",
                message_code="file_not_found",
                entity="File",
                identifier="name",
                identifier_value=name,
            )
        return path

    async def _publish(self, staged: Path, name: str, size: int) -> None:
        """Copy a staged file and expose it atomically at its final name.

        Args:
            staged: Validated upload owned by the operation.
            name: Generated content digest and extension.
            size: Verified byte count of the staged file.

        Returns:
            None. Concurrent publication of the same content reuses the file.

        Raises:
            OSError: The copy or local publication failed.
        """
        directory = self.root / name[:2]
        path = AsyncPath(directory / name)
        await AsyncPath(directory).mkdir(
            mode=0o700, parents=True, exist_ok=True
        )
        if await path.is_file():
            return

        async with TemporaryDirectory(dir=str(directory)) as temp:
            copy = Path(temp) / "content"
            async with self.reader.open_bytes(staged) as source:
                copied = await self.writer.write_stream(
                    copy, self.reader.chunks(source), mode="xb"
                )
            if copied != size:
                raise OSError("The stored copy does not match the upload size")
            try:
                await path.hardlink_to(copy)
            except FileExistsError:
                if not await path.is_file():
                    raise

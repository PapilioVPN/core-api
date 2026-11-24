"""Private receipt files over the shared local Storage adapter."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from anyio.abc import ByteReceiveStream
from papilio.errors.exceptions import NotFoundException

from src.apps.core.storage.files.domain.results.staging import StagedFile
from src.apps.core.storage.files.infra.local import LocalFileStorage

from ..domain.enums.images import ImageFormat


class ReceiptFiles:
    def __init__(self, root: Path) -> None:
        self.stores = {
            format: LocalFileStorage(root=root / format)
            for format in ImageFormat
        }

    async def save(self, format: ImageFormat, data: StagedFile) -> None:
        """Publish staged bytes once at their private content address.

        Args:
            format: Format verified against the staged bytes.
            data: Staged bytes kept alive by the caller.

        Returns:
            None. Equal images reuse their existing address.
        """
        await self.stores[format].save_if_absent(data)

    @asynccontextmanager
    async def open(
        self, format: ImageFormat, digest: str
    ) -> AsyncIterator[ByteReceiveStream]:
        """Open the stored image until the consumer finishes streaming.

        Args:
            format: Format segment of the authorized address.
            digest: Validated lowercase SHA-256 digest.

        Returns:
            A stream starting at byte zero.

        Raises:
            NotFoundException: The address has no stored image.
        """
        storage = self.stores[format]
        try:
            async with storage.open(
                storage.root / digest[:2] / digest
            ) as file:
                yield file
        except FileNotFoundError as error:
            raise NotFoundException(
                message="Receipt image not found",
                message_code="receipt_image_not_found",
                entity="receipt_image",
                identifier="digest",
                identifier_value=digest,
            ) from error

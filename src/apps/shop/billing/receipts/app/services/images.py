"""Validate staged receipt images before private publication."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import partial

from anyio.abc import ByteReceiveStream
from papilio.errors.exceptions import NotFoundException, ValidationException

from src.apps.core.storage.files.app.interfaces.private import IPrivateFiles
from src.apps.core.storage.files.domain.results.staging import StagedFile
from src.shared.utils.asyncio.processes import ProcessRunner
from src.shared.utils.images import mime_checker

from ...domain.enums.images import ImageFormat


class ReceiptImages:
    def __init__(self, files: IPrivateFiles, processes: ProcessRunner) -> None:
        self.files = files
        self.processes = processes

    async def upload(
        self, source: ByteReceiveStream, format: ImageFormat, *, max_bytes: int
    ) -> str:
        """Validate and store one image without buffering it in memory.

        Args:
            source: Borrowed stream containing the original image.
            format: Image format declared by the caller.
            max_bytes: Configured upload limit in bytes.

        Returns:
            The stored image's SHA-256 digest.

        Raises:
            ValidationException: The image cannot be decoded as declared.
        """
        digest = await self.files.upload(
            source,
            format.value,
            max_bytes=max_bytes,
            validator=partial(self._validate, format=format),
        )
        return digest

    @asynccontextmanager
    async def open(
        self, format: ImageFormat, digest: str
    ) -> AsyncIterator[ByteReceiveStream]:
        """Open stored bytes using an authorized format and digest.

        Args:
            format: Image format from the registered address.
            digest: Validated lowercase SHA-256 digest.

        Returns:
            An operation-owned stream context.
        """
        try:
            async with self.files.open(format.value, digest) as source:
                yield source
        except FileNotFoundError as error:
            raise NotFoundException(
                message="Receipt image not found",
                message_code="receipt_image_not_found",
                entity="receipt_image",
                identifier="digest",
                identifier_value=digest,
            ) from error

    async def _validate(
        self, staged: StagedFile, *, format: ImageFormat
    ) -> None:
        valid = await self.processes.run(
            mime_checker, staged.path, format.mime_type
        )
        if not valid:
            raise ValidationException(
                message="Invalid receipt image",
                message_code="receipt_image_invalid",
                loc=["image"],
            )

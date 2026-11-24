"""Validate staged receipt images before private publication."""

from contextlib import AbstractAsyncContextManager

from anyio.abc import ByteReceiveStream
from papilio.errors.exceptions import ValidationException

from src.apps.core.storage.files.infra.staging import FileStager
from src.shared.utils.asyncio.processes import ProcessRunner
from src.shared.utils.images import mime_checker

from ...domain.enums.images import ImageFormat
from ...infra.local import ReceiptFiles


class ReceiptImages:
    def __init__(
        self, stager: FileStager, processes: ProcessRunner, files: ReceiptFiles
    ) -> None:
        self.stager = stager
        self.processes = processes
        self.files = files

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
        async with self.stager.stage(source, max_bytes=max_bytes) as staged:
            valid = await self.processes.run(
                mime_checker, staged.path, format.mime_type
            )
            if not valid:
                raise ValidationException(
                    message="Invalid receipt image",
                    message_code="receipt_image_invalid",
                    loc=["image"],
                )
            await self.files.save(format, staged)
        return staged.sha256

    def open(
        self, format: ImageFormat, digest: str
    ) -> AbstractAsyncContextManager[ByteReceiveStream]:
        """Open stored bytes using an authorized format and digest.

        Args:
            format: Image format from the registered address.
            digest: Validated lowercase SHA-256 digest.

        Returns:
            An operation-owned stream context.
        """
        return self.files.open(format, digest)

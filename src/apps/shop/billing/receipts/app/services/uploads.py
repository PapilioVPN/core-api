"""Validate receipt images through the existing file upload owner."""

from functools import partial

from anyio.abc import ByteReceiveStream
from papilio.errors.exceptions import ValidationException

from src.apps.core.storage.files.app.interfaces.uploads import IFileUpload
from src.apps.core.storage.files.domain.results.staging import StagedFile
from src.apps.core.storage.files.domain.results.uploads import FileUploadResult
from src.shared.utils.asyncio.processes import ProcessRunner
from src.shared.utils.images import mime_checker

from ...domain.dtos.uploads import ReceiptUpload


class ReceiptUploadService:
    def __init__(self, files: IFileUpload, processes: ProcessRunner) -> None:
        """Bind the existing uploader and image decoding runner."""
        self.files = files
        self.processes = processes

    async def upload(
        self, source: ByteReceiveStream, data: ReceiptUpload, *, max_bytes: int
    ) -> FileUploadResult:
        """Store validated receipt image bytes.

        Args:
            source: Borrowed stream, closed by the caller.
            data: Original name and declared JPEG, PNG or WebP MIME.
            max_bytes: Maximum number of bytes to stage.

        Returns:
            Committed file and its stable storage URL.

        Raises:
            ValidationException: The image fails to decode as declared.
        """
        result = await self.files.upload(
            source,
            data,
            max_bytes=max_bytes,
            validator=partial(self._validate, mime_type=data.mime_type),
        )
        return result

    async def _validate(self, data: StagedFile, *, mime_type: str) -> None:
        """Check the actual MIME and decode staged bytes before publication."""
        valid = await self.processes.run(mime_checker, data.path, mime_type)
        if not valid:
            raise ValidationException(
                message="Receipt image does not match the declared type",
                message_code="receipt_image_invalid",
                loc=["image"],
            )

"""Validate receipt images through the existing file upload owner."""

from anyio.abc import ByteReceiveStream
from papilio.errors.exceptions import ValidationException

from src.apps.core.storage.files.app.interfaces.uploads import IFileUpload
from src.apps.core.storage.files.domain.results.uploads import FileUploadResult
from src.shared.utils.asyncio.processes import ProcessRunner
from src.shared.utils.images import validate_image

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
            validator=lambda staged: validate_image(
                staged.path,
                data.mime_type,
                processes=self.processes,
                error=ValidationException(
                    message="Receipt image does not match the declared type",
                    message_code="receipt_image_invalid",
                    loc=["image"],
                ),
            ),
        )
        return result

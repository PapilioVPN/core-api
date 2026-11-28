"""Apply receipt image validation to the shared Storage upload."""

from anyio.abc import ByteReceiveStream
from papilio.errors.exceptions import ValidationException

from src.apps.core.storage.files.app.interfaces.uploads import IFileUpload
from src.apps.core.storage.files.domain.results.uploads import FileUploadResult
from src.shared.utils.asyncio.processes import ProcessRunner
from src.shared.utils.images import validate_image

from ...domain.dtos.uploads import ReceiptUpload


class ReceiptUploadService:
    def __init__(self, files: IFileUpload, processes: ProcessRunner) -> None:
        self.files = files
        self.processes = processes

    async def upload(
        self, source: ByteReceiveStream, data: ReceiptUpload, *, max_bytes: int
    ) -> FileUploadResult:
        """Check the staged image before Storage publishes it.

        Args:
            source: Borrowed stream owned by the caller.
            data: Validated file name and declared image type.
            max_bytes: Byte limit enforced while staging.

        Returns:
            The stored file metadata and its stable URL.

        Raises:
            ValidationException: The bytes do not decode as the declared type.
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

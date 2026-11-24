"""Recognize a registered receipt outside the SQL request."""

from anyio import BrokenResourceError, IncompleteRead
from anyio.streams.buffered import BufferedByteReceiveStream
from papilio.core.config import StorageConfig
from papilio.errors.base import APPException

from src.apps.core.storage.files.app.interfaces.downloads import IFileDownload
from src.apps.shop.billing.receipts.domain.enums.extraction import (
    ExtractionStatus,
)

from ...domain.parsers.receipts import fields
from ...domain.results.records import OCRFailure, OCROutcome
from ..executions.records import OCRExecution
from ..interfaces.gateways import IOCRGateway


class OCRPipeline:
    def __init__(
        self,
        execution: OCRExecution,
        files: IFileDownload,
        gateway: IOCRGateway,
        storage: StorageConfig,
    ) -> None:
        """Bind short SQL execution, existing Storage and the OCR gateway."""
        self.execution = execution
        self.files = files
        self.gateway = gateway
        self.max_bytes = storage.max_file_size

    async def process(self, receipt_id: int, *, event_id: str) -> None:
        """Process one receipt event and record its extraction outcome.

        Args:
            receipt_id: Receipt whose stored image is eligible for recognition.
            event_id: Durable publication identity, stable on redelivery.

        Returns:
            None once committed or skipped.
        """
        source = await self.execution.prepare(receipt_id, event_id)
        if source is not None:
            outcome = await self.extract(source.file_id)
            await self.execution.complete(receipt_id, event_id, outcome)

    async def extract(self, file_id: int | None) -> OCROutcome:
        """Read original bytes and extract only supported, explicit values.

        Args:
            file_id: Registered Storage identity, or None for a missing image.

        Returns:
            Extraction outcome with only confidently recognized, explicit
            values.
        """
        if file_id is None:
            return OCROutcome(
                ExtractionStatus.FAILED, error_code="image_unavailable"
            )
        try:
            async with self.files.open(file_id) as download:
                size = download.metadata.size_bytes
                if not 0 < size <= self.max_bytes:
                    return OCROutcome(
                        ExtractionStatus.FAILED,
                        error_code="image_size_invalid",
                    )
                stream = BufferedByteReceiveStream(download.source)
                image = await stream.receive_exactly(size)
        except (APPException, OSError, IncompleteRead, BrokenResourceError):
            return OCROutcome(
                ExtractionStatus.FAILED, error_code="image_unavailable"
            )

        lines = await self.gateway.read(image)
        if isinstance(lines, OCRFailure):
            return OCROutcome(ExtractionStatus.FAILED, error_code=lines.code)
        result = fields(lines)
        status = (
            ExtractionStatus.EXTRACTED
            if any(
                value is not None
                for value in (
                    result.amount,
                    result.tracking_code,
                    result.reference_code,
                )
            )
            else ExtractionStatus.UNREADABLE
        )
        return OCROutcome(status, result)

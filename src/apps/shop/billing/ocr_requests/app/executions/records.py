"""Use short native requests before and after receipt recognition."""

from dishka import AsyncContainer
from papilio.infra.db.tools.decorators import transactional
from papilio.infra.scopes import Inject, request_scoped

from src.apps.core.storage.files.app.interfaces.services import IFileService
from src.apps.shop.billing.receipts.app.interfaces.services import (
    IReceiptService,
)

from ...domain.models.records import OCRRequestModel
from ...domain.results.records import OCROutcome, OCRSource
from ..interfaces.services import IOCRRequestService


class OCRExecution:
    def __init__(self, container: AsyncContainer) -> None:
        """Use the application container for short native SQL scopes."""
        self.container = container

    @request_scoped
    async def prepare(
        self,
        receipt_id: int,
        event_id: str,
        *,
        requests: IOCRRequestService = Inject(),
        receipts: IReceiptService = Inject(),
        files: IFileService = Inject(),
    ) -> OCRSource | None:
        """Resolve an unprocessed receipt event to its Storage file.

        Args:
            receipt_id: Identity carried by ReceiptCreated.
            event_id: Durable identity of the delivery.
            requests: Request-scoped attempt service.
            receipts: Receipt record owner.
            files: Storage metadata service.

        Returns:
            A source whose file ID can be absent, or None when already handled
            or when the receipt is gone.
        """
        source = None
        handled = await requests.exists_by_event(event_id)
        if not handled:
            receipt = await receipts.find_by_id(receipt_id)
            if receipt is not None:
                file_id = await files.find_id_by_url(receipt.image_url)
                source = OCRSource(file_id)
        return source

    @request_scoped
    @transactional
    async def complete(
        self,
        receipt_id: int,
        event_id: str,
        outcome: OCROutcome,
        *,
        requests: IOCRRequestService = Inject(),
        receipts: IReceiptService = Inject(),
    ) -> None:
        """Commit a new attempt and its receipt update together.

        Args:
            receipt_id: Identity of the processed receipt.
            event_id: Durable identity used to suppress repeated writes.
            outcome: Terminal extraction status and observed fields.
            requests: Request-scoped attempt service.
            receipts: Receipt record owner on the same transaction.

        Returns:
            None after applying or skipping the completion.
        """
        record = await requests.create(
            OCRRequestModel(
                receipt_id=receipt_id,
                event_id=event_id,
                status=outcome.status,
                error_code=outcome.error_code,
            )
        )
        if record is not None:
            await receipts.save_extraction(
                receipt_id, outcome.status, outcome.fields
            )

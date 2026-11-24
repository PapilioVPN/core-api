"""OCR attempt fields returned to authorized Shop operators."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput

from src.apps.shop.billing.receipts.domain.enums.extraction import (
    ExtractionStatus,
)


class OCRRequestOutput(BaseOutput):
    id: int
    receipt_id: int
    status: ExtractionStatus
    error_code: str | None
    created_at: datetime

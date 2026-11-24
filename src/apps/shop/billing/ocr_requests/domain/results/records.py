"""Values carried between receipt lookup, OCR and persistence."""

from dataclasses import dataclass

from src.apps.shop.billing.receipts.domain.enums.extraction import (
    ExtractionStatus,
)
from src.apps.shop.billing.receipts.domain.results.extraction import (
    ReceiptFields,
)


@dataclass(frozen=True, slots=True)
class OCRSource:
    file_id: int | None


@dataclass(frozen=True, slots=True)
class OCROutcome:
    status: ExtractionStatus
    fields: ReceiptFields = ReceiptFields()
    error_code: str | None = None

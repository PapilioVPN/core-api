"""Paging and exact filters for completed OCR attempts."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType, PageType, PerPageType

from src.apps.shop.billing.receipts.domain.enums.extraction import (
    ExtractionStatus,
)


class OCRRequestPage(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    status: ExtractionStatus | None = None


class OCRRequestList(OCRRequestPage):
    receipt_id: IdType | None = None

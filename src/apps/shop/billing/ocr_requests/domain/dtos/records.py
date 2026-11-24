"""Paging and exact filters for completed OCR attempts."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType, PageType, PerPageType

from src.apps.shop.billing.receipts.domain.enums.extraction import (
    ExtractionStatus,
)


class OCRRequestList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    receipt_id: IdType | None = None
    status: ExtractionStatus | None = None

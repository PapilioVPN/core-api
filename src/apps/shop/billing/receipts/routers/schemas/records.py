"""Stored receipt evidence presented to authorized Shop operators."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput

from ...domain.enums.extraction import ExtractionStatus
from ...domain.enums.records import ReceiptStatus


class ReceiptOutput(BaseOutput):
    id: int
    image_url: str
    status: ReceiptStatus
    extraction_status: ExtractionStatus | None
    amount: int | None
    paid_at: datetime | None
    tracking_code: str | None
    reference_code: str | None
    bank_name: str | None
    source_last4: str | None
    destination_last4: str | None
    created_at: datetime
    updated_at: datetime

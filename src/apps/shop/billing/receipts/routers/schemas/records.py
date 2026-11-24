"""Receipt details returned after registration."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput


class ReceiptOutput(BaseOutput):
    id: int
    image_url: str
    amount: int | None
    paid_at: datetime | None
    created_at: datetime
    updated_at: datetime

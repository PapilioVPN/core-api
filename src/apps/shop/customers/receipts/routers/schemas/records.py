"""Details of a registered customer receipt."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput


class ReceiptOutput(BaseOutput):
    id: int
    customer_id: int
    amount: int
    image_url: str
    status: str
    created_at: datetime

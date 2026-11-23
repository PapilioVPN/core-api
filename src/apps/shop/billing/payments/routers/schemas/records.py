"""Payment details exposed to authorized billing operators."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput

from ...domain.enums.records import PaymentSource, PaymentStatus


class PaymentOutput(BaseOutput):
    id: int
    customer_id: int
    source: PaymentSource
    source_id: int
    amount: int
    status: PaymentStatus
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime

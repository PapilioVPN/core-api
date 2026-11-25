"""Gateway metadata visible to authorized operators."""

from datetime import datetime
from decimal import Decimal

from papilio.schemas.outputs import BaseOutput


class GatewayOutput(BaseOutput):
    id: int
    key: str
    title: str
    kind: str | None
    price_currency: str | None
    pay_currency: str | None
    rial_rate: Decimal | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

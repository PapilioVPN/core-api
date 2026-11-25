"""Crypto payment records returned to the Shop panel."""

from datetime import datetime
from decimal import Decimal

from papilio.schemas.outputs import BaseOutput

from ...domain.enums.records import CryptoPaymentStatus


class PaymentOutput(BaseOutput):
    id: int
    gateway_id: int
    amount: int
    price_amount: Decimal
    price_currency: str
    pay_currency: str | None
    invoice_id: str | None
    invoice_url: str | None
    provider_payment_id: str | None
    status: CryptoPaymentStatus
    confirmed_at: datetime | None
    created_at: datetime
    updated_at: datetime

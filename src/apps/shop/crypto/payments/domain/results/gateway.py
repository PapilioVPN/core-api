"""Materialized invoice and settlement facts from an authenticated gateway."""

from dataclasses import dataclass
from decimal import Decimal

from ..enums.records import CryptoPaymentStatus


@dataclass(frozen=True, slots=True)
class GatewayInvoice:
    id: str
    url: str


@dataclass(frozen=True, slots=True)
class GatewayNotice:
    payment_id: str
    invoice_id: str | None
    status: CryptoPaymentStatus | None


@dataclass(frozen=True, slots=True)
class GatewayPayment:
    id: str
    invoice_id: str | None
    order_id: str | None
    status: CryptoPaymentStatus | None
    price_amount: Decimal
    price_currency: str
    pay_amount: Decimal
    pay_currency: str
    actually_paid: Decimal | None

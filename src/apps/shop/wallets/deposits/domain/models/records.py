"""An expiring invoice for a wallet top-up."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from src.apps.shop.banking.payment_cards.domain.enums.records import (
    PaymentMode,
)
from src.apps.shop.crypto.gateways.domain.dtos.configs import PriceCurrency


@dataclass(frozen=True, slots=True)
class CardPayment:
    final_amount: int
    mode: PaymentMode
    card_number: str
    holder_name: str
    bank_id: int
    bank_title: str
    bank_icon_url: str | None
    confirmation_code: str | None = None
    payment_id: int | None = None
    method: Literal["card_to_card"] = "card_to_card"
    currency: Literal["IRR"] = "IRR"


@dataclass(frozen=True, slots=True)
class PlisioPayment:
    gateway_id: int
    gateway_title: str
    gateway_icon_url: str | None
    currency: PriceCurrency
    final_amount: Decimal
    invoice_url: str
    payment_id: int
    method: Literal["plisio"] = "plisio"


type DepositPayment = CardPayment | PlisioPayment


@dataclass(frozen=True, slots=True)
class DepositInvoice:
    id: UUID
    customer_id: int
    amount: int
    created_at: datetime
    expires_at: datetime
    payment: DepositPayment

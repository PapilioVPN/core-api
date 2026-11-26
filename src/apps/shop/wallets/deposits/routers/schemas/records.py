"""Wallet top-up invoices returned to authorized operators."""

from datetime import datetime
from decimal import Decimal
from math import ceil
from typing import Annotated, Literal
from uuid import UUID

from papilio.schemas.outputs import BaseOutput
from papilio.utils.dates import utc_now
from pydantic import Field, computed_field

from src.apps.shop.banking.payment_cards.domain.enums.records import (
    PaymentMode,
)
from src.apps.shop.crypto.gateways.domain.dtos.configs import PriceCurrency


class CardPaymentOutput(BaseOutput):
    method: Literal["card_to_card"]
    mode: PaymentMode
    currency: Literal["IRR"]
    final_amount: int
    card_number: str
    holder_name: str
    bank_id: int
    bank_title: str
    bank_icon_url: str | None
    confirmation_code: str | None


class PlisioPaymentOutput(BaseOutput):
    method: Literal["plisio"]
    gateway_id: int
    gateway_title: str
    gateway_icon_url: str | None
    currency: PriceCurrency
    final_amount: Decimal
    invoice_url: str


class DepositOutput(BaseOutput):
    id: UUID
    customer_id: int
    amount: int
    created_at: datetime
    expires_at: datetime
    payment: Annotated[
        CardPaymentOutput | PlisioPaymentOutput, Field(discriminator="method")
    ]

    @computed_field
    @property
    def expires_in(self) -> int:
        """Return the seconds remaining when this response is serialized."""
        remaining = (self.expires_at - utc_now()).total_seconds()
        return max(0, ceil(remaining))

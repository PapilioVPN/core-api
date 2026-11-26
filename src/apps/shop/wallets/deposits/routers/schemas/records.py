"""Wallet top-up invoices returned to authorized operators."""

from datetime import datetime
from math import ceil
from typing import Literal
from uuid import UUID

from papilio.schemas.outputs import BaseOutput
from papilio.utils.dates import utc_now
from pydantic import computed_field

from src.apps.shop.banking.payment_cards.domain.enums.records import (
    PaymentMode,
)


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


class DepositOutput(BaseOutput):
    id: UUID
    customer_id: int
    amount: int
    created_at: datetime
    expires_at: datetime
    payment: CardPaymentOutput

    @computed_field
    @property
    def expires_in(self) -> int:
        """Return the seconds remaining when this response is serialized."""
        remaining = (self.expires_at - utc_now()).total_seconds()
        return max(0, ceil(remaining))

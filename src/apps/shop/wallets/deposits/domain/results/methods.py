"""Payment options for an original wallet top-up amount."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from src.apps.shop.banking.payment_cards.domain.enums.records import (
    PaymentMode,
)
from src.apps.shop.crypto.gateways.domain.results.methods import GatewayOption


@dataclass(frozen=True, slots=True)
class CardOption:
    mode: PaymentMode
    currency: Literal["IRR"] = "IRR"


@dataclass(frozen=True, slots=True)
class PaymentOptions:
    customer_id: int
    amount: int
    card_to_card: CardOption | None
    gateways: Sequence[GatewayOption]
    total_gateways: int
    currency: Literal["IRR"] = "IRR"

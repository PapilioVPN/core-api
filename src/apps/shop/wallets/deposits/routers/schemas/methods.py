"""Payment selection data for the top-up form."""

from typing import Literal

from papilio.schemas.outputs import BaseOutput

from src.apps.shop.banking.payment_cards.domain.enums.records import (
    PaymentMode,
)
from src.apps.shop.crypto.gateways.domain.dtos.configs import PriceCurrency


class CardOptionOutput(BaseOutput):
    mode: PaymentMode
    currency: Literal["IRR"]


class GatewayOptionOutput(BaseOutput):
    id: int
    kind: str
    title: str
    icon_url: str | None
    min_amount: int | None
    max_amount: int | None
    price_currency: PriceCurrency


class MethodsOutput(BaseOutput):
    customer_id: int
    amount: int
    currency: Literal["IRR"]
    card_to_card: CardOptionOutput | None
    gateways: list[GatewayOptionOutput]

"""Credential-free gateway options for payment selection."""

from dataclasses import dataclass

from ..dtos.configs import PriceCurrency


@dataclass(frozen=True, slots=True)
class GatewayOption:
    id: int
    kind: str
    title: str
    icon_url: str | None
    min_amount: int | None
    max_amount: int | None
    price_currency: PriceCurrency

"""A hosted invoice and the prepared inputs for Plisio issuance."""

from dataclasses import dataclass, field
from decimal import Decimal

from src.apps.shop.crypto.gateways.domain.dtos.configs import (
    NowPaymentsConfig,
    PlisioConfig,
    PriceCurrency,
)


@dataclass(frozen=True, slots=True)
class Invoice:
    id: str
    url: str


@dataclass(frozen=True, slots=True)
class PlisioIssue:
    payment_id: int
    amount: Decimal
    currency: PriceCurrency
    config: PlisioConfig = field(repr=False)
    expire_minutes: int | None = None


@dataclass(frozen=True, slots=True)
class NowPaymentsIssue:
    payment_id: int
    amount: Decimal
    config: NowPaymentsConfig = field(repr=False)

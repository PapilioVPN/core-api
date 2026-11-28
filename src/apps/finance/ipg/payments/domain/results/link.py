"""Inputs and materialized outcomes of one provider link issuance."""

from dataclasses import dataclass

from pydantic import SecretStr

from ..enums.records import LinkStatus


@dataclass(frozen=True, slots=True)
class LinkRequest:
    payment_id: int
    merchant_id: SecretStr
    amount: int
    description: str
    callback_url: str


@dataclass(frozen=True, slots=True)
class ProviderLink:
    status: LinkStatus
    reference: str | None = None
    url: str | None = None


@dataclass(frozen=True, slots=True)
class PaymentLink:
    id: int
    status: LinkStatus
    url: str | None

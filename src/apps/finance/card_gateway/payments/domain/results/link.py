"""Materialized link creation input and outcomes."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from ....gateways.domain.dtos.configs import VarizaLinkConfig


@dataclass(frozen=True, slots=True)
class Link:
    slug: str
    pay_url: str
    expires_at: datetime | None


@dataclass(frozen=True, slots=True)
class LinkRequest:
    amount: int
    config: VarizaLinkConfig


class LinkFailure(StrEnum):
    NOT_FOUND = "not_found"
    GATEWAY_UNAVAILABLE = "gateway_unavailable"
    EXPIRED = "expired"
    INVALID_AMOUNT = "invalid_amount"
    INVALID_RETURN_URL = "invalid_return_url"
    REJECTED = "rejected"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class LinkResult:
    link: Link | None = None
    failure: LinkFailure | None = None


@dataclass(frozen=True, slots=True)
class LinkPreparation:
    result: LinkResult
    request: LinkRequest | None = None

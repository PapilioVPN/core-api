"""Immutable details of a temporary rial invoice preview."""

from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

from src.apps.shop.products.durations.domain.enums.start import DurationStart


@dataclass(frozen=True, slots=True)
class Topup:
    kind: Literal["topup"] = "topup"


@dataclass(frozen=True, slots=True)
class Catalog:
    catalog_id: int
    service_id: int
    service_title: str
    title: str
    volume_bytes: int | None
    days: int | None
    starts_on: DurationStart | None
    kind: Literal["catalog"] = "catalog"


@dataclass(frozen=True, slots=True)
class VolumeRange:
    range_id: int
    service_id: int
    service_title: str
    volume_bytes: int
    days: int | None
    kind: Literal["range"] = "range"


type Details = Annotated[
    Topup | Catalog | VolumeRange, Field(discriminator="kind")
]


@dataclass(frozen=True, slots=True)
class Terms:
    amount: int
    details: Details


@dataclass(frozen=True, slots=True)
class Invoice:
    id: UUID
    customer_id: int
    amount: int
    details: Details
    expires_at: datetime

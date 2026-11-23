"""Public catalog data for the storefront."""

from dataclasses import dataclass

from src.apps.shop.products.durations.domain.enums.start import DurationStart


@dataclass(frozen=True, slots=True)
class PublicCatalog:
    id: int
    service_id: int
    service_title: str
    title: str
    price: int
    volume_bytes: int | None
    duration_days: int | None
    starts_on: DurationStart | None

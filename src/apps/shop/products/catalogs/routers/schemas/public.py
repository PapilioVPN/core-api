"""Storefront catalog fields exposed over HTTP."""

from papilio.schemas.outputs import BaseOutput

from src.apps.shop.products.durations.domain.enums.start import DurationStart


class PublicCatalogOutput(BaseOutput):
    """Offer with price in rials, volume in bytes and duration in days."""

    id: int
    service_id: int
    service_title: str
    title: str
    price: int
    volume_bytes: int | None
    duration_days: int | None
    starts_on: DurationStart | None

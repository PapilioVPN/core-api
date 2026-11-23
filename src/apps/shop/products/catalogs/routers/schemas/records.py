"""Catalog profiles and selected sale terms for the panel."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput

from src.apps.shop.products.catalogs.domain.enums.records import CatalogStatus
from src.apps.shop.products.durations.routers.schemas.records import (
    DurationOutput,
)
from src.apps.shop.products.volumes.routers.schemas.records import VolumeOutput


class CatalogOutput(BaseOutput):
    id: int
    service_id: int
    title: str
    price: int
    priority: int
    status: CatalogStatus
    volume_id: int | None
    duration_id: int | None
    created_at: datetime
    updated_at: datetime


class CatalogDetailOutput(BaseOutput):
    catalog: CatalogOutput
    volume: VolumeOutput | None
    duration: DurationOutput | None

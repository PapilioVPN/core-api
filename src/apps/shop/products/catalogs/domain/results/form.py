"""Initial selections for the catalog editor."""

from dataclasses import dataclass

from papilio.schemas.results import PagedType

from src.apps.shop.products.durations.domain.models.records import (
    DurationModel,
)
from src.apps.shop.products.services.domain.models.records import ServiceModel
from src.apps.shop.products.volumes.domain.models.records import VolumeModel


@dataclass(frozen=True, slots=True)
class CatalogForm:
    services: PagedType[ServiceModel]
    volumes: PagedType[VolumeModel]
    durations: PagedType[DurationModel]

"""Catalog detail and its immutable sale definitions."""

from dataclasses import dataclass

from src.apps.shop.catalogs.domain.models.records import CatalogModel
from src.apps.shop.durations.domain.models.records import DurationModel
from src.apps.shop.volumes.domain.models.records import VolumeModel


@dataclass(frozen=True, slots=True)
class CatalogDetail:
    catalog: CatalogModel
    volume: VolumeModel | None
    duration: DurationModel | None

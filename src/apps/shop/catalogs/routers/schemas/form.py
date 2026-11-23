"""Initial choice pages and constraints for creating a catalog."""

from papilio.schemas.outputs import BaseOutput, EnumOut

from src.apps.shop.catalogs.domain.dtos.records import MIN_PRICE
from src.apps.shop.durations.routers.schemas.records import DurationOutput
from src.apps.shop.services.routers.schemas.records import ServiceOutput
from src.apps.shop.volumes.routers.schemas.records import VolumeOutput


class ChoicePage[T: BaseOutput](BaseOutput):
    items: list[T]
    total_items: int


class CatalogFormOutput(BaseOutput):
    services: ChoicePage[ServiceOutput]
    volumes: ChoicePage[VolumeOutput]
    durations: ChoicePage[DurationOutput]
    per_page: int
    statuses: list[EnumOut]
    min_price: int = MIN_PRICE
    currency: str = "IRR"

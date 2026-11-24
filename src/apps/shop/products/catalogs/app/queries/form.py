"""Compose the catalog editor's service, volume and duration pages."""

from src.apps.shop.products.catalogs.domain.results.form import CatalogForm
from src.apps.shop.products.durations.app.interfaces.services import (
    IDurationService,
)
from src.apps.shop.products.durations.domain.dtos.records import DurationList
from src.apps.shop.products.services.app.interfaces.services import (
    IShopService,
)
from src.apps.shop.products.services.domain.dtos.records import ServiceList
from src.apps.shop.products.volumes.app.interfaces.services import (
    IVolumeService,
)
from src.apps.shop.products.volumes.domain.dtos.records import VolumeList


class CatalogFormQuery:
    def __init__(
        self,
        services: IShopService,
        volumes: IVolumeService,
        durations: IDurationService,
    ) -> None:
        """Bind the three owners of editor selections."""
        self.services = services
        self.volumes = volumes
        self.durations = durations

    async def form(self, per_page: int) -> CatalogForm:
        """Read bounded first pages for all three editor pickers.

        Args:
            per_page: Validated maximum rows in each selection list.

        Returns:
            Service, volume, and duration pages with independent totals.
        """
        services = await self.services.list(ServiceList(per_page=per_page))
        volumes = await self.volumes.list(VolumeList(per_page=per_page))
        durations = await self.durations.list(DurationList(per_page=per_page))
        return CatalogForm(services, volumes, durations)

"""Read catalog details, SQL search results, and editor choices."""

from papilio.infra.db.transaction import active_transaction
from papilio.schemas.results import PagedType
from papilio.tools.checks import Checks

from src.apps.shop.catalogs.domain.dtos.search import CatalogSearch
from src.apps.shop.catalogs.domain.models.records import CatalogModel
from src.apps.shop.catalogs.domain.results.details import CatalogDetail
from src.apps.shop.catalogs.domain.results.filters import CatalogOptions
from src.apps.shop.catalogs.domain.results.form import CatalogForm
from src.apps.shop.catalogs.infra.pg.readers.panel import CatalogReader
from src.apps.shop.catalogs.infra.redis.repositories.details import (
    CatalogCache,
)
from src.apps.shop.durations.app.interfaces.services import IDurations
from src.apps.shop.durations.domain.dtos.records import DurationList
from src.apps.shop.services.app.interfaces.services import IServices
from src.apps.shop.services.domain.dtos.records import ServiceList
from src.apps.shop.volumes.app.interfaces.services import IVolumes
from src.apps.shop.volumes.domain.dtos.records import VolumeList


class CatalogQuery(Checks[CatalogDetail]):
    entity = "Catalog"
    ttl = 300

    def __init__(
        self,
        reader: CatalogReader,
        cache: CatalogCache,
        services: IServices,
        volumes: IVolumes,
        durations: IDurations,
    ) -> None:
        """Bind panel reads and the optional detail cache."""
        self.reader = reader
        self.cache = cache
        self.services = services
        self.volumes = volumes
        self.durations = durations

    async def get_by_id(self, id: int) -> CatalogDetail:
        """Read one catalog detail with read-through caching.

        Args:
            id: Stored catalog identity.

        Returns:
            The detail. Application transactions read and fill from SQL only.

        Raises:
            NotFoundException: The catalog is absent.
        """
        use_cache = active_transaction() is None
        detail = await self.cache.find(id) if use_cache else None
        if detail is None:
            detail = await self.reader.get_by_id(id)
            detail = self._check_for_existence("id", id, detail)
            if use_cache:
                await self.cache.store(detail, self.ttl)
        return detail

    async def list(self, data: CatalogSearch) -> PagedType[CatalogModel]:
        """Read the selected page from current SQL records.

        Args:
            data: Validated filters, paging and sorting.

        Returns:
            Matching records and their total.
        """
        page = await self.reader.list(data)
        return page

    async def options(self, data: CatalogSearch) -> CatalogOptions:
        """Read the choices for a catalog search.

        Args:
            data: Validated query with the current search text.

        Returns:
            Facets over text matches before paging and selected filters.
        """
        options = await self.reader.options(data.q)
        return options

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

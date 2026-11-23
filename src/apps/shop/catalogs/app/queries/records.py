"""Read scalar and set catalog details through the record cache."""

from collections.abc import Sequence

from papilio.infra.db.transaction import active_transaction
from papilio.tools.checks import Checks

from src.apps.shop.catalogs.app.interfaces.cache import ICatalogCache
from src.apps.shop.catalogs.domain.results.details import CatalogDetail
from src.apps.shop.catalogs.infra.pg.readers.details import CatalogReader


class CatalogQuery(Checks[CatalogDetail]):
    entity = "Catalog"
    ttl = 300

    def __init__(
        self,
        reader: CatalogReader,
        cache: ICatalogCache,
    ) -> None:
        """Bind the detail reader and its cache."""
        self.reader = reader
        self.cache = cache

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

    async def get_by_ids(self, ids: Sequence[int]) -> Sequence[CatalogDetail]:
        """Return each existing detail once, in first-requested order."""
        keys = list(dict.fromkeys(ids))
        use_cache = active_transaction() is None
        details = await self.cache.find_many(keys) if use_cache else {}
        missing = [id for id in keys if id not in details]
        if missing:
            rows = await self.reader.get_by_ids(missing)
            details.update((row.catalog.id, row) for row in rows)
            if use_cache:
                await self.cache.store_many(rows, self.ttl)
        return [details[id] for id in keys if id in details]

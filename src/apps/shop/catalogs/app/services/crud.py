"""Authoritative catalog record operations through one repository."""

from collections.abc import Sequence

from papilio.infra.db.tools.decorators import transactional
from papilio.tools.checks import IDChecks

from src.apps.shop.catalogs.app.decorators.records import forget_cache
from src.apps.shop.catalogs.app.interfaces.cache import ICatalogCache
from src.apps.shop.catalogs.domain.dtos.records import CatalogPatch
from src.apps.shop.catalogs.domain.models.records import CatalogModel
from src.apps.shop.catalogs.infra.pg.repositories.crud import (
    CatalogRepository,
)


class CatalogCRUD(IDChecks[CatalogModel]):
    entity = "Catalog"

    def __init__(self, repo: CatalogRepository, cache: ICatalogCache) -> None:
        """Bind the request repository and independent detail cache."""
        self.repo = repo
        self.cache = cache

    async def get_by_id(self, id: int) -> CatalogModel:
        """Read a required catalog from PostgreSQL by its identity."""
        catalog = await self.find_by_id(id)
        catalog = self._check_for_id_existence(id, catalog)
        return catalog

    async def find_by_id(self, id: int) -> CatalogModel | None:
        """Read a catalog record without requiring its existence."""
        catalog = await self.repo.get_by_id(id)
        return catalog

    async def get_by_ids(self, ids: Sequence[int]) -> Sequence[CatalogModel]:
        """Read a bounded set of records, omitting absent identities."""
        catalogs = await self.repo.get_by_ids(ids) if ids else []
        return catalogs

    @forget_cache.one
    @transactional
    async def create(self, data: CatalogModel) -> CatalogModel:
        """Persist a catalog whose service and terms were resolved by app.

        Args:
            data: Prepared catalog record with server-resolved references.

        Returns:
            Stored catalog with its assigned identity and timestamps.
        """
        catalog = await self.repo.create(data)
        return catalog

    @forget_cache.one
    @transactional
    async def update(self, id: int, data: CatalogPatch) -> CatalogModel:
        """Apply supplied record fields and resolved term identities.

        Args:
            id: Stored catalog identity.
            data: Validated profile fields and prepared volume/duration IDs.
                Null clears a term, while omission preserves it.

        Returns:
            The updated catalog.

        Raises:
            ValidationException: No recognized fields were supplied.
            NotFoundException: The identity is absent.
        """
        changes = self._check_not_empty_dict(data.to_row())
        catalog = await self.repo.update_by_id(id, changes)
        catalog = self._check_for_id_existence(id, catalog)
        return catalog

    @forget_cache.one
    @transactional
    async def remove(self, id: int) -> CatalogModel:
        """Remove one catalog and return its previous record."""
        catalog = await self.repo.remove_by_id(id)
        catalog = self._check_for_id_existence(id, catalog)
        return catalog

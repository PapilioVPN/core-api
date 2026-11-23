"""Detail cache operations used by the catalog query and CRUD service."""

from collections.abc import Sequence
from typing import Protocol

from src.apps.shop.catalogs.domain.results.details import CatalogDetail


class ICatalogCache(Protocol):
    async def find(self, id: int) -> CatalogDetail | None: ...

    async def find_many(
        self, ids: Sequence[int]
    ) -> dict[int, CatalogDetail]: ...

    async def store(self, detail: CatalogDetail, ttl: int) -> None: ...

    async def store_many(
        self, details: Sequence[CatalogDetail], ttl: int
    ) -> None: ...

    async def forget(self, id: int) -> None: ...


class ICatalogCacheOwner(Protocol):
    @property
    def cache(self) -> ICatalogCache: ...

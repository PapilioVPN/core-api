"""Authoritative operations on catalog records."""

from collections.abc import Sequence
from typing import Protocol

from src.apps.shop.products.catalogs.domain.models.records import CatalogModel

from ...domain.dtos.records import CatalogPatch, DurationRef, VolumeRef


class ICatalogService(Protocol):
    async def create(self, data: CatalogModel) -> CatalogModel: ...

    async def update(self, id: int, data: CatalogPatch) -> CatalogModel: ...

    async def remove(self, id: int) -> CatalogModel: ...

    async def get_by_id(self, id: int) -> CatalogModel: ...

    async def find_by_id(self, id: int) -> CatalogModel | None: ...

    async def get_by_ids(
        self, ids: Sequence[int]
    ) -> Sequence[CatalogModel]: ...


class ICatalogTermsService(Protocol):
    async def volume_id(self, data: VolumeRef) -> int | None: ...

    async def duration_id(self, data: DurationRef) -> int | None: ...

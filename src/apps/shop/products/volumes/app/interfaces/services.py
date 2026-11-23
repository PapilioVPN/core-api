"""Reusable volume operations shared with other shop capabilities."""

from collections.abc import Sequence
from typing import Protocol

from papilio.schemas.results import PagedType

from src.apps.shop.products.volumes.domain.dtos.records import (
    VolumeCreate,
    VolumeList,
)
from src.apps.shop.products.volumes.domain.models.records import VolumeModel


class IVolumeCRUD(Protocol):
    async def create(self, data: VolumeCreate) -> VolumeModel: ...

    async def get_by_id(self, id: int) -> VolumeModel: ...

    async def find_by_id(self, id: int) -> VolumeModel | None: ...

    async def get_by_ids(
        self, ids: Sequence[int]
    ) -> Sequence[VolumeModel]: ...

    async def list(self, query: VolumeList) -> PagedType[VolumeModel]: ...

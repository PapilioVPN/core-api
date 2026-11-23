"""Reusable volume operations shared with other shop capabilities."""

from typing import Protocol

from papilio.schemas.results import PagedType

from src.apps.shop.volumes.domain.dtos.records import VolumeCreate, VolumeList
from src.apps.shop.volumes.domain.models.records import VolumeModel


class IVolumes(Protocol):
    async def create(self, data: VolumeCreate) -> VolumeModel: ...

    async def get_by_id(self, id: int) -> VolumeModel: ...

    async def list(self, query: VolumeList) -> PagedType[VolumeModel]: ...

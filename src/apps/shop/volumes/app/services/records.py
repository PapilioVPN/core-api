"""Create and read immutable volume definitions."""

from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks

from src.apps.shop.volumes.domain.dtos.records import VolumeCreate, VolumeList
from src.apps.shop.volumes.domain.models.records import VolumeModel
from src.apps.shop.volumes.infra.pg.repositories.records import (
    VolumeRepository,
)


class Volumes(IDChecks[VolumeModel]):
    entity = "Volume"

    def __init__(self, repo: VolumeRepository) -> None:
        """Bind the request's volume repository."""
        self.repo = repo

    @transactional
    async def create(self, data: VolumeCreate) -> VolumeModel:
        """Register one reusable volume definition.

        Args:
            data: Validated fixed size in bytes.

        Returns:
            The stored volume with its identity and creation time.
        """
        volume = await self.repo.save(VolumeModel(**data.to_row()))
        return volume

    async def get_by_id(self, id: int) -> VolumeModel:
        """Read a reusable volume by its stable identity.

        Args:
            id: Stored volume identity.

        Returns:
            The stored definition.

        Raises:
            NotFoundException: The identity is absent.
        """
        volume = await self.repo.get_by_id(id)
        volume = self._check_for_id_existence(id, volume)
        return volume

    async def list(self, query: VolumeList) -> PagedType[VolumeModel]:
        """Read volume definitions for the panel's selection list.

        Args:
            query: Validated size filter and page bounds.

        Returns:
            Matching volume definitions and their total.
        """
        page = await self.repo.list(
            limit=query.per_page,
            offset=(query.page - 1) * query.per_page,
            size_bytes=query.size_bytes,
        )
        return page

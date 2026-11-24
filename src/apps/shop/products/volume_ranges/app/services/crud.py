"""Authoritative operations for stored volume range records."""

from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks
from papilio.types.constants import INT64_MAX

from src.apps.shop.products.volume_ranges.domain.dtos.records import (
    RangeList,
    RangeWrite,
)
from src.apps.shop.products.volume_ranges.domain.models.records import (
    VolumeRangeModel,
)
from src.apps.shop.products.volume_ranges.infra.pg.repositories.crud import (
    VolumeRangeRepository,
)


class VolumeRangeService(IDChecks[VolumeRangeModel]):
    entity = "VolumeRange"

    def __init__(self, repo: VolumeRangeRepository) -> None:
        """Bind the current request's range repository."""
        self.repo = repo

    @transactional
    async def create(self, data: VolumeRangeModel) -> VolumeRangeModel:
        """Store a prepared range under its service.

        Args:
            data: Prepared range with validated bounds and rate.

        Returns:
            The stored range with its assigned identity.
        """
        row = await self.repo.create(data)
        return row

    async def get_by_id(self, service_id: int, id: int) -> VolumeRangeModel:
        """Read a range under its selected service.

        Args:
            service_id: Required parent identity.
            id: Stored range identity.

        Returns:
            The stored range.

        Raises:
            NotFoundException: The range is absent under that service.
        """
        row = await self.repo.get(service_id, id)
        row = self._check_for_id_existence(id, row)
        return row

    async def list(
        self, service_id: int, data: RangeList
    ) -> PagedType[VolumeRangeModel]:
        """Read a page of owned ranges for the panel.

        Args:
            service_id: Required parent identity.
            data: Validated volume filter and page selection.

        Returns:
            Filtered ranges and their total.
        """
        page = await self.repo.list(
            service_id,
            limit=data.per_page,
            offset=min((data.page - 1) * data.per_page, INT64_MAX),
            volume_bytes=data.volume_bytes,
        )
        return page

    @transactional
    async def replace(
        self, service_id: int, id: int, data: RangeWrite
    ) -> VolumeRangeModel:
        """Replace a range with an entire validated definition.

        Args:
            service_id: Required parent identity.
            id: Target range identity.
            data: New bounds, duration, rate and activity.

        Returns:
            Updated range with the original identity.
        """
        row = await self.repo.replace(
            service_id, id, data.to_row(exclude_unset=False)
        )
        row = self._check_for_id_existence(id, row)
        return row

    @transactional
    async def remove(self, service_id: int, id: int) -> VolumeRangeModel:
        """Remove one range under the selected service.

        Args:
            service_id: Required parent identity.
            id: Target range identity.

        Returns:
            The removed range.
        """
        row = await self.repo.remove_in_service(service_id, id)
        row = self._check_for_id_existence(id, row)
        return row

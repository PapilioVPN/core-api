"""List the volume choices available to a customer."""

from papilio.schemas.results import PagedType
from papilio.tools.checks import Checks

from src.apps.shop.products.volume_ranges.domain.models.records import (
    VolumeRangeModel,
)
from src.apps.shop.products.volume_ranges.infra.pg.readers.public import (
    PublicRangeReader,
)


class PublicRangeQuery(Checks[PagedType[VolumeRangeModel]]):
    entity = "Service"

    def __init__(self, reader: PublicRangeReader) -> None:
        """Bind the request's public range reader."""
        self.reader = reader

    async def list(
        self, service_id: int, *, page: int, per_page: int
    ) -> PagedType[VolumeRangeModel]:
        """Read one page of active range choices under one service.

        Args:
            service_id: Required service identity.
            page: Validated one-based page.
            per_page: Validated size of each page.

        Returns:
            The visible ranges and their total.

        Raises:
            NotFoundException: The owning service is absent or inactive.
        """
        result = await self.reader.list(
            service_id, limit=per_page, offset=(page - 1) * per_page
        )
        result = self._check_for_existence("id", service_id, result)
        return result

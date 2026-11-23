"""Find the current sale rule for a selected volume."""

from papilio.infra.db.repositories.backends.postgresql import PGReader
from sqlmodel import col

from src.apps.shop.volume_ranges.domain.models.records import VolumeRangeModel
from src.apps.shop.volume_ranges.infra.pg.sql.public import visible_ranges
from src.apps.shop.volume_ranges.infra.pg.tables import VolumeRangeTable


class QuoteReader(PGReader):
    async def find(
        self, service_id: int, volume_bytes: int
    ) -> VolumeRangeModel | None:
        """Read the single active rule that contains the selected volume.

        Args:
            service_id: Required owning service.
            volume_bytes: Selected volume in bytes.

        Returns:
            The authoritative rule, or None when the choice is unavailable.
        """
        rule = VolumeRangeTable
        stmt = visible_ranges(service_id).where(
            col(rule.min_bytes) <= volume_bytes,
            col(rule.max_bytes) >= volume_bytes,
        )
        result = await self.uow.execute(stmt)
        row = result.scalar_one_or_none()
        return row

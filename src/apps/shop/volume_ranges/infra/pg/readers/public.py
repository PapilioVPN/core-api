"""Read customer-selectable ranges for an active service."""

from papilio.infra.db.repositories.backends.postgresql import PGReader
from papilio.schemas.results import PagedType
from sqlalchemy import and_, func, select
from sqlmodel import col

from src.apps.shop.services.infra.pg.tables import ServiceTable
from src.apps.shop.volume_ranges.domain.models.records import VolumeRangeModel
from src.apps.shop.volume_ranges.infra.pg.sql.public import visible_ranges
from src.apps.shop.volume_ranges.infra.pg.tables import VolumeRangeTable


class PublicRangeReader(PGReader):
    async def list(
        self, service_id: int, *, limit: int, offset: int
    ) -> PagedType[VolumeRangeModel] | None:
        """Read visible ranges and their total from the selected parent.

        Args:
            service_id: Required owning service identity.
            limit: Maximum number of ranges.
            offset: Matching ranges to skip.

        Returns:
            A page, possibly empty, or None when the parent is unavailable.
        """
        rule = VolumeRangeTable
        service = ServiceTable
        stmt = (
            select(func.count(col(rule.id)))
            .select_from(service)
            .outerjoin(
                rule,
                and_(
                    col(rule.service_id) == col(service.id),
                    col(rule.is_active).is_(True),
                ),
            )
            .where(
                col(service.id) == service_id, col(service.is_active).is_(True)
            )
            .group_by(col(service.id))
        )
        result = await self.uow.execute(stmt)
        total = result.scalar_one_or_none()
        page = None
        if total is not None:
            items: list[VolumeRangeModel] = []
            if offset < total:
                stmt = (
                    visible_ranges(service_id)
                    .order_by(col(rule.min_bytes), col(rule.id))
                    .limit(limit)
                    .offset(offset)
                )
                rows = await self.uow.execute(stmt)
                items = list(rows.scalars().all())
            page = PagedType(items=items, total_items=total)
        return page

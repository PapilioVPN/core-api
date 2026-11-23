"""SQL visibility shared by range listing and price lookup."""

from sqlalchemy import Select, select
from sqlmodel import col

from src.apps.shop.products.services.infra.pg.tables import ServiceTable
from src.apps.shop.products.volume_ranges.infra.pg.tables import (
    VolumeRangeTable,
)


def visible_ranges(service_id: int) -> Select[tuple[VolumeRangeTable]]:
    """Select ranges that can be offered on one service.

    Args:
        service_id: Required owning service.

    Returns:
        SQL selection for active ranges on the active parent service.
    """
    rule = VolumeRangeTable
    stmt = (
        select(rule)
        .join(ServiceTable, col(ServiceTable.id) == col(rule.service_id))
        .where(
            col(rule.service_id) == service_id,
            col(rule.is_active).is_(True),
            col(ServiceTable.is_active).is_(True),
        )
    )
    return stmt

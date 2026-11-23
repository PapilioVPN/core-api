"""Select the public fields of published offers on active services."""

from sqlalchemy import Nullable, Select, select
from sqlmodel import col

from src.apps.shop.products.catalogs.domain.enums.records import CatalogStatus
from src.apps.shop.products.catalogs.infra.pg.tables import CatalogTable
from src.apps.shop.products.durations.domain.enums.start import DurationStart
from src.apps.shop.products.durations.infra.pg.tables import DurationTable
from src.apps.shop.products.services.infra.pg.tables import ServiceTable
from src.apps.shop.products.volumes.infra.pg.tables import VolumeTable

type CatalogRow = tuple[
    int, int, str, str, int, int | None, int | None, DurationStart | None
]


def visible_catalogs() -> Select[CatalogRow]:
    """Build the shared public offer projection.

    Args:
        None.

    Returns:
        The query for published offers under active services, with optional
        volume and duration projected alongside each offer.
    """
    table = CatalogTable
    stmt = (
        select(
            col(table.id),
            col(table.service_id),
            col(ServiceTable.title),
            col(table.title),
            col(table.price),
            Nullable(col(VolumeTable.size_bytes)),
            Nullable(col(DurationTable.days)),
            Nullable(col(DurationTable.starts_on)),
        )
        .select_from(table)
        .join(ServiceTable, col(ServiceTable.id) == col(table.service_id))
        .outerjoin(VolumeTable, col(VolumeTable.id) == col(table.volume_id))
        .outerjoin(
            DurationTable, col(DurationTable.id) == col(table.duration_id)
        )
        .where(
            col(table.status) == CatalogStatus.PUBLISHED,
            col(ServiceTable.is_active).is_(True),
        )
    )
    return stmt

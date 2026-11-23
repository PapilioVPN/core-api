"""Select catalog records with their fixed volume and duration."""

from sqlalchemy import Select, select
from sqlmodel import col

from src.apps.shop.products.catalogs.infra.pg.tables import CatalogTable
from src.apps.shop.products.durations.infra.pg.tables import DurationTable
from src.apps.shop.products.volumes.infra.pg.tables import VolumeTable


def details() -> Select[tuple[CatalogTable, VolumeTable, DurationTable]]:
    """Join the optional sale definitions for scalar and set reads."""
    table = CatalogTable
    return (
        select(table, VolumeTable, DurationTable)
        .outerjoin(VolumeTable, col(VolumeTable.id) == col(table.volume_id))
        .outerjoin(
            DurationTable, col(DurationTable.id) == col(table.duration_id)
        )
    )

"""Volume table discovered by Papilio."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import Index, text

from src.apps.shop.volumes.domain.models.records import VolumeModel


class VolumeTable(VolumeModel, BaseTable, table=True):
    __table_args__ = (
        Index(
            "uq_volumes_terms",
            "size_bytes",
            unique=True,
            postgresql_where=text("is_canonical"),
        ),
    )

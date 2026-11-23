"""Custom volume ranges discovered by Papilio."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import Index, text
from sqlalchemy.dialects.postgresql import ExcludeConstraint

from src.apps.shop.products.volume_ranges.domain.models.records import (
    VolumeRangeModel,
)

OVERLAP_CONSTRAINT = "excl_volume_ranges_overlap"


class VolumeRangeTable(VolumeRangeModel, BaseTable, table=True):
    __table_args__ = (
        Index("ix_volume_ranges_service", "service_id", "min_bytes"),
        ExcludeConstraint(
            (text("numrange(service_id, service_id, '[]')"), "="),
            (text("int8range(min_bytes, max_bytes, '[]')"), "&&"),
            name=OVERLAP_CONSTRAINT,
            using="gist",
        ),
    )

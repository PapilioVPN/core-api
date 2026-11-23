"""Duration storage discovered by Papilio."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import Index, text

from src.apps.shop.products.durations.domain.models.records import (
    DurationModel,
)


class DurationTable(DurationModel, BaseTable, table=True):
    __table_args__ = (
        Index(
            "uq_durations_terms",
            "days",
            "starts_on",
            unique=True,
            postgresql_where=text("is_canonical"),
        ),
    )

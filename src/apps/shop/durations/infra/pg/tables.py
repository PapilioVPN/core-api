"""Duration storage discovered by Papilio."""

from papilio.infra.db.table import BaseTable

from src.apps.shop.durations.domain.models.records import DurationModel


class DurationTable(DurationModel, BaseTable, table=True):
    pass

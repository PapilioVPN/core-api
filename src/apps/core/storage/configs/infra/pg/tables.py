"""One shared destination record, with database-enforced cardinality."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import Index, text

from src.apps.core.storage.configs.domain.models.storage import (
    StorageConfigModel,
)


class StorageConfigTable(StorageConfigModel, BaseTable, table=True):
    __table_args__ = (
        Index("uq_storage_configs_singleton", text("(true)"), unique=True),
    )

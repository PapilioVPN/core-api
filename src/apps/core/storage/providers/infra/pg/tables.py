"""One-to-one S3 settings with at most one active storage connection."""

from typing import Optional

from papilio.infra.db.table import BaseTable
from sqlalchemy import Index, text
from sqlmodel import Relationship

from src.apps.core.storage.providers.domain.models.records import (
    StorageProviderConfigModel,
    StorageProviderModel,
)


class StorageProviderTable(StorageProviderModel, BaseTable, table=True):
    __table_args__ = (
        Index(
            "uq_storage_providers_active",
            "is_active",
            unique=True,
            postgresql_where=text("is_active"),
        ),
    )
    configuration: Optional["StorageProviderConfigTable"] = Relationship(
        back_populates="provider",
        sa_relationship_kwargs={
            "uselist": False,
            "lazy": "raise",
            "passive_deletes": "all",
        },
    )


class StorageProviderConfigTable(
    StorageProviderConfigModel, BaseTable, table=True
):
    provider: StorageProviderTable = Relationship(
        back_populates="configuration",
        sa_relationship_kwargs={"lazy": "raise"},
    )

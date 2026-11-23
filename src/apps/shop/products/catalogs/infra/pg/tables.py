"""Catalog table discovered by Papilio."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import Index

from src.apps.shop.products.catalogs.domain.models.records import CatalogModel


class CatalogTable(CatalogModel, BaseTable, table=True):
    __table_args__ = (
        Index("ix_catalogs_service", "service_id", "status", "priority", "id"),
    )

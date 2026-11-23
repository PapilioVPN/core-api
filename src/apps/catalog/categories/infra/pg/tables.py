"""Category persistence registered by Papilio."""

from papilio.infra.db.table import BaseTable

from src.apps.catalog.categories.domain.models.records import CategoryModel


class CategoryTable(CategoryModel, BaseTable, table=True):
    pass

"""Attributes and category bindings registered by Papilio."""

from papilio.infra.db.table import BaseTable
from sqlmodel import Relationship

from src.apps.catalog.attributes.domain.models.categories import (
    CategoryAttributeModel,
)
from src.apps.catalog.attributes.domain.models.records import AttributeModel


class AttributeTable(AttributeModel, BaseTable, table=True):
    pass


class CategoryAttributeTable(CategoryAttributeModel, BaseTable, table=True):
    attribute: AttributeTable = Relationship(
        sa_relationship_kwargs={"lazy": "joined", "innerjoin": True}
    )

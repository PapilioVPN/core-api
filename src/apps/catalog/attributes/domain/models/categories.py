"""Attribute bindings identified by their category and feature."""

from papilio.infra.db.schema.entity import BaseEntity
from papilio.infra.db.schema.fields import BoolField, ForeignKeyField, IntField


class CategoryAttributeModel(BaseEntity):
    category_id: int = ForeignKeyField(
        "tbl_categories.id", ondelete="CASCADE", primary_key=True
    )
    attribute_id: int = ForeignKeyField(
        "tbl_attributes.id", ondelete="CASCADE", primary_key=True, index=True
    )
    is_required: bool = BoolField(default=False)
    is_filterable: bool = BoolField(default=False)
    is_variant_axis: bool = BoolField(default=False)
    priority: int = IntField(default=0)

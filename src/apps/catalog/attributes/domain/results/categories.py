"""A category's assigned attribute and settings for panel reads."""

from dataclasses import dataclass

from src.apps.catalog.attributes.domain.models.records import AttributeModel


@dataclass(frozen=True, slots=True)
class BindingDetail:
    category_id: int
    attribute_id: int
    is_required: bool
    is_filterable: bool
    is_variant_axis: bool
    priority: int
    attribute: AttributeModel

"""HTTP output for a category's assigned features."""

from papilio.schemas.outputs import BaseOutput

from src.apps.catalog.attributes.routers.schemas.records import AttributeOutput


class BindingOutput(BaseOutput):
    category_id: int
    attribute_id: int
    is_required: bool
    is_filterable: bool
    is_variant_axis: bool
    priority: int


class BindingDetailOutput(BindingOutput):
    attribute: AttributeOutput

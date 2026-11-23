"""Controls for assigning a feature to one category."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IntType, PageType, PerPageType


class BindingSave(BaseDTO):
    is_required: bool = False
    is_filterable: bool = False
    is_variant_axis: bool = False
    priority: IntType = 0


class BindingList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20

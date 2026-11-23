"""Panel search inputs for customer profiles."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType, PageType, PerPageType, ValueType


class ProfileSearch(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    q: ValueType | None = None
    group_id: IdType | None = None
    is_blocked: bool | None = None

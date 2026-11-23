"""Customer search for offers within one service."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import PageType, PerPageType, ValueType


class ServiceCatalogSearch(BaseDTO):
    q: ValueType | None = None
    is_unlimited: bool | None = None
    has_expiry: bool | None = None
    page: PageType = 1
    per_page: PerPageType = 20

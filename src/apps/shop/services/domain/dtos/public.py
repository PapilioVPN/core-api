"""Validated storefront browsing for services."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import PageType, PerPageType, ValueType


class PublicServiceSearch(BaseDTO):
    q: ValueType | None = None
    page: PageType = 1
    per_page: PerPageType = 20

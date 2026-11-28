"""Filters for the panel's bank reference list."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import PageType, PerPageType, ValueType


class BankList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    q: ValueType | None = None
    is_active: bool | None = None

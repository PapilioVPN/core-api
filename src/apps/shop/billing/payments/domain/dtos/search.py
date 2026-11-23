"""Filters and pagination for the panel's payment list."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType, PageType, PerPageType

from ..enums.records import PaymentSource, PaymentStatus


class PaymentSearch(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    customer_id: IdType | None = None
    source: PaymentSource | None = None
    source_id: IdType | None = None
    status: PaymentStatus | None = None

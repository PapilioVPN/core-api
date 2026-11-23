"""Panel filters and paging inputs for customer payments."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType, PageType, PerPageType, ValueType

from ..enums.records import PaymentStatus


class PaymentSearch(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    q: ValueType | None = None
    customer_id: IdType | None = None
    card_id: IdType | None = None
    status: PaymentStatus | None = None

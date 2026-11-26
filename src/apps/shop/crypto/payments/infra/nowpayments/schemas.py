"""The payment facts supplied by a finished NOWPayments notification."""

from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType
from pydantic import Field

PaymentRef = Annotated[
    str, Field(min_length=1, max_length=64, coerce_numbers_to_str=True)
]


class NowPayment(BaseDTO):
    order_id: IdType
    invoice_id: PaymentRef
    payment_id: PaymentRef
    price_amount: Annotated[Decimal, Field(gt=0)]
    price_currency: str
    pay_amount: Annotated[Decimal, Field(gt=0)]
    actually_paid: Annotated[Decimal, Field(ge=0)]


class NotificationStatus(StrEnum):
    FINISHED = "finished"
